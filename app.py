from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Workout, WorkoutEntry, Meal, FoodItem
from config import Config
from werkzeug.security import check_password_hash
from datetime import datetime
from sqlalchemy.orm import joinedload


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

# REGISTER ROUTE
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        age = request.form.get('age', type=int)
        weight = request.form.get('weight', type=float)
        height = request.form.get('height', type=float)
        goal = request.form['goal']

        if User.query.filter_by(email=email).first():
            flash('Email already registered! Please login.', 'error')
            return redirect(url_for('login'))

        user = User(name=name, email=email, age=age, weight=weight, height=height, goal=goal)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Try again!', 'error')
    return render_template('login.html')

# LOGOUT ROUTE
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

from datetime import date
from sqlalchemy.orm import joinedload

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    # Workouts today
    workouts_today = Workout.query.filter_by(user_id=current_user.id, workout_date=today).count()
    # Meals today
    meals_today = Meal.query.filter_by(user_id=current_user.id, date=today).count()
    # Calories consumed today
    meals = Meal.query.options(joinedload(Meal.food_item)).filter_by(user_id=current_user.id, date=today).all()
    calories_in_today = sum(
        (meal.food_item.calories_per_100g or 0) * (float(meal.quantity) / 100.0)
        for meal in meals if meal.food_item
    )
    # Calories burned today
    entries = db.session.query(
        WorkoutEntry.sets, WorkoutEntry.reps, WorkoutEntry.intensity, User.weight
    ).select_from(WorkoutEntry) \
        .join(Workout, WorkoutEntry.workout_id == Workout.id) \
        .join(User, Workout.user_id == User.id) \
        .filter(User.id == current_user.id, Workout.workout_date == today).all()
    calories_burned_today = 0
    for sets, reps, intensity, weight in entries:
        multiplier = {'low': 3, 'medium': 5, 'high': 8}.get(intensity.lower(), 5)
        calories_burned_today += sets * reps * multiplier * float(weight) * 0.0001

    stats = {
        'workouts_today': workouts_today,
        'meals_today': meals_today,
        'calories_in_today': round(calories_in_today, 2),
        'calories_burned_today': round(calories_burned_today, 2)
    }
    return render_template('dashboard.html', stats=stats)


# LOG WORKOUT (Protected)
@app.route('/log_workout', methods=['GET', 'POST'])
@login_required
def log_workout():
    if request.method == 'POST':
        workout_date = request.form['workout_date']
        workout_type = request.form['workout_type']
        exercise = request.form['exercise']
        sets = int(request.form['sets'])
        reps = int(request.form['reps'])
        intensity = request.form['intensity']

        workout = Workout(
            user_id=current_user.id,
            workout_date=workout_date,
            workout_type=workout_type
        )
        db.session.add(workout)
        db.session.commit()

        entry = WorkoutEntry(
            workout_id=workout.id,
            exercise=exercise,
            sets=sets,
            reps=reps,
            intensity=intensity
        )
        db.session.add(entry)
        db.session.commit()

        flash("Workout logged!", 'success')
        return redirect(url_for('dashboard'))
    return render_template('log_workout.html')

# LOG MEAL (Protected)
@app.route('/log_meal', methods=['GET', 'POST'])
@login_required
def log_meal():
    food_items = FoodItem.query.all()
    if request.method == 'POST':
        quantity = request.form['quantity']
        meal_type = request.form['meal_type']
        date = request.form['date']

        food_item_id = request.form.get('food_item_id')
        new_food_name = request.form.get('new_food_name')
        new_food_calories = request.form.get('new_food_calories')
        new_food_protein = request.form.get('new_food_protein')

        if not food_item_id and new_food_name and new_food_calories and new_food_protein:
            new_item = FoodItem(
                name=new_food_name,
                calories_per_100g=int(new_food_calories),
                protein=int(new_food_protein)
            )
            db.session.add(new_item)
            db.session.commit()
            food_item_id = new_item.id
        elif food_item_id:
            food_item_id = int(food_item_id)
        else:
            flash("Please select or add a food item.", 'error')
            return redirect(url_for('log_meal'))

        meal = Meal(
            user_id=current_user.id,
            food_item_id=food_item_id,
            quantity=quantity,
            meal_type=meal_type,
            date=date
        )
        db.session.add(meal)
        db.session.commit()
        flash("Meal logged!", 'success')
        return redirect(url_for('dashboard'))

    return render_template('log_meal.html', food_items=food_items)

from datetime import datetime
from sqlalchemy.orm import joinedload

@app.route('/summary', methods=['GET', 'POST'])
@login_required
def summary():
    summary = None
    summary_date = None
    meals = []
    workouts = []

    if request.method == 'POST':
        summary_date = request.form['summary_date']
        date_obj = datetime.strptime(summary_date, "%Y-%m-%d").date()

        # Meals
        meals = Meal.query.options(joinedload(Meal.food_item)) \
            .filter_by(user_id=current_user.id, date=date_obj).all()
        calories_in = 0
        for meal in meals:
            try:
                qty = float(meal.quantity)
                cals = (meal.food_item.calories_per_100g or 0) * (qty / 100)
                calories_in += cals
            except Exception as e:
                print("Meal error:", e, meal)
                continue

        # Workouts
        all_workouts = Workout.query.filter_by(user_id=current_user.id, workout_date=date_obj).all()
        workout_entries = []
        for w in all_workouts:
            for entry in w.entries:
                entry.workout_type = w.workout_type
                workout_entries.append(entry)

        calories_burned = 0
        for entry in workout_entries:
            try:
                sets = int(entry.sets)
                weight_kg = float(current_user.weight)
                intensity = entry.intensity.lower()
                MET = {'low': 3, 'medium': 5, 'high': 8}.get(intensity, 5)
                # Assign average minutes per set based on intensity
                minutes_per_set = {'low': 0.67, 'medium': 1.2, 'high': 2}.get(intensity, 1)
                duration = sets * minutes_per_set  # total minutes for this exercise
                calories_burned += MET * weight_kg * 0.0175 * duration
            except Exception as e:
                print("Workout error:", e, entry)
                continue

        summary = {
            "calories_in": round(calories_in, 2),
            "calories_burned": round(calories_burned, 2),
            "net": round(calories_in - calories_burned, 2)
        }
        workouts = workout_entries

        for meal in meals:
            print("Meal:", meal.food_item.name, "| Calories/100g:", meal.food_item.calories_per_100g, "| Qty:", meal.quantity)

    return render_template('summary.html', summary=summary, summary_date=summary_date, meals=meals, workouts=workouts)



# AI COACH (Protected)
from huggingface_hub import InferenceClient

@app.route('/ai_coach', methods=['GET', 'POST'])
@login_required
def ai_coach():
    answer = None
    if request.method == 'POST':
        question = request.form['question']
        try:
            client = InferenceClient(token=os.getenv('HF_API_KEY'))
            messages = [
                {"role": "system", "content": "You are a professional fitness coach. Give concise, practical, and safe advice. Keep answers focused and helpful."},
                {"role": "user", "content": question}
            ]
            response = client.chat.completions.create(
                model="Qwen/Qwen2.5-72B-Instruct",
                messages=messages,
                max_tokens=500
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"Error: {e}"
    return render_template('ai_coach.html', answer=answer)

# ------------- Run Server -------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
