import mysql.connector
import calendar
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, get_flashed_messages
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'secret_keypay'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'bayadwise_database'
}


def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('fullname')
        username = request.form.get('username')
        password = request.form.get('password')

        if not full_name or not username or not password:
            flash("All fields are required", "error")
            return redirect(url_for('register'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash("Username is already taken, please try again", "error")
            return redirect(url_for('register'))

        # Default role is 'user'
        cursor.execute(
            "INSERT INTO users (full_name, username, password, role, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (full_name, username, password, 'user')
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        flash("Incorrect input, please try again.", "error")
        return redirect(url_for('index'))

    # Check password
    if password != user['password']:
        flash("Incorrect input, please try again.", "error")
        return redirect(url_for('index'))

    # Login successful, save session
    session['user_id'] = user['user_id']
    session['role'] = user['role']
    session['username'] = user['username']

    # Redirect based on role
    if user['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('dashboard'))


@app.route('/admin')
def admin_dashboard():
    # Only allow admins
    if session.get('role') != 'admin':
        return "Access denied", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all users
    cursor.execute(
        "SELECT user_id, full_name, username, password, role FROM users ORDER BY user_id")
    users = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    cursor.execute("SELECT COUNT(*) AS total_bills FROM bills")
    total_bills = cursor.fetchone()['total_bills']

    cursor.close()
    conn.close()

    return render_template(
        'admin.html',
        users=users,
        total_users=total_users,
        total_bills=total_bills
    )


@app.route('/dashboard')
def dashboard():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    last_month_date = today.replace(day=1) - timedelta(days=1)
    last_month = last_month_date.month
    last_year = last_month_date.year

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    username = session.get('username')

    # Bills
    cursor.execute(
        "SELECT * FROM bills WHERE user_id=%s ORDER BY due_date", (user_id,))
    bills_data = cursor.fetchall()

    # total_bills =

    total_bills = sum(int(b['amount']) for b in bills_data)
    total_paid = sum(int(b['amount'])
                     for b in bills_data if b['status'] == 'Paid')
    total_unpaid = total_bills - total_paid

    # Your Share
    split_among = session.get('split_among', 1)
    your_share = total_bills // split_among

    # Ipon Progress
    today_date = datetime.now().date()
    current_month = today_date.month
    cursor.execute(
        "SELECT saved_amount, goal_amount FROM ipon WHERE user_id=%s AND month=%s",
        (user_id, current_month)
    )
    ipon_row = cursor.fetchone()
    saved_amount = int(ipon_row['saved_amount']) if ipon_row else 0
    goal_amount = int(ipon_row['goal_amount']) if ipon_row else 0
    ipon_progress = f"{saved_amount}/{your_share + goal_amount}"

    # CURRENT MONTH BILLS
    cursor.execute(
        "SELECT bill_name, amount, status, due_date FROM bills "
        "WHERE user_id=%s AND MONTH(due_date)=%s AND YEAR(due_date)=%s",
        (user_id, current_month, current_year)
    )
    current_bills = cursor.fetchall()
    total_current = sum(int(b['amount']) for b in current_bills)
    split_among = session.get('split_among', 1)
    your_share = total_current // split_among if split_among else total_current
    top_expense = max([int(b['amount']) for b in current_bills], default=0)

    # LAST MONTH BILLS
    cursor.execute(
        "SELECT amount FROM bills WHERE user_id=%s AND MONTH(due_date)=%s AND YEAR(due_date)=%s",
        (user_id, last_month, last_year)
    )
    last_month_bills = cursor.fetchall()
    total_last = sum(int(b['amount']) for b in last_month_bills)

    # FORECAST
    cursor.execute(
        "SELECT amount FROM bills WHERE user_id=%s AND due_date < %s",
        (user_id, datetime(current_year, current_month, 1))
    )
    past_bills = cursor.fetchall()
    if past_bills:
        avg_past = int(sum(int(b['amount'])
                       for b in past_bills) / len(past_bills))
    else:
        avg_past = 0

    forecast_this_month = max(total_current, avg_past)
    difference = forecast_this_month - total_last

    #  NOTIFICATIONS MODAL

    # Bill Reminder
    cursor.execute("""
        SELECT bill_name, due_date
        FROM bills
        WHERE user_id=%s AND status='Unpaid' AND due_date >= %s
        ORDER BY due_date ASC
        LIMIT 1
    """, (user_id, today_date))
    nearest_bill = cursor.fetchone()

    if nearest_bill:
        due_date = nearest_bill['due_date'].date() if hasattr(
            nearest_bill['due_date'], "date") else nearest_bill['due_date']
        days_left = (due_date - today_date).days
        bill_reminder_text = f"{nearest_bill['bill_name']} bill due in {days_left} day(s). Almost there!"
    else:
        bill_reminder_text = "No upcoming unpaid bills 🎉"

    # Ipon Notification Text
    ipon_total_goal = your_share + goal_amount

    if ipon_total_goal > 0:
        percent = (saved_amount / ipon_total_goal) * 100

        if percent >= 75:
            ipon_message = "Almost there!"
        elif percent >= 50:
            ipon_message = "Halfway there!"
        elif percent > 0:
            ipon_message = "Just getting started!"
        else:
            ipon_message = "Start saving today 💸"

        ipon_text = f"{ipon_message} You’ve saved ₱{int(saved_amount)} out of ₱{int(ipon_total_goal)}."
    else:
        ipon_text = "No Ipon goal set yet."

    # Forecast Notification
    if total_current > total_last:
        forecast_text = "Spending is higher than last month 📈"
    elif total_current < total_last:
        forecast_text = "Good job! You’re spending less this month 📉"
    else:
        forecast_text = "Your spending is consistent this month ⚖️"

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        bills=bills_data,
        total_bills=total_current,
        your_share=your_share,
        ipon_progress=ipon_progress,
        last_month_total=total_last,
        forecast_this_month=forecast_this_month,
        difference=difference,
        payments=current_bills,
        top_expense=top_expense,
        bill_reminder_text=bill_reminder_text,
        ipon_text=ipon_text,
        forecast_text=forecast_text,
        username=username
    )

# --- BILLS PAGE ---


@app.route('/bills', methods=['GET'])
def bills():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    if 'user_id' not in session or session.get('role') == 'admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all bills
    cursor.execute(
        "SELECT * FROM bills WHERE user_id=%s ORDER BY due_date", (user_id,))
    bills_data = cursor.fetchall()

    total_bills = sum(int(b['amount']) for b in bills_data)
    total_paid = sum(int(b['amount'])
                     for b in bills_data if b['status'] == 'Paid')
    total_unpaid = total_bills - total_paid

    split_among = session.get('split_among', 1)
    your_share = total_bills / split_among if split_among else 0

    cursor.close()
    conn.close()

    total_bills = int(total_bills)
    total_paid = int(total_paid)
    total_unpaid = int(total_unpaid)
    your_share = int(your_share)

    return render_template(
        'bills.html',
        bills=bills_data,
        total_bills=total_bills,
        total_paid=total_paid,
        total_unpaid=total_unpaid,
        split_among=split_among,
        your_share=your_share
    )

#  ADD / TOGGLE / DELETE BILLS


@app.route('/bill_action', methods=['POST'])
def bill_action():
    action = request.form.get('action')
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if action == 'add':
            bill_name = request.form.get('bill_name')
            amount = float(request.form.get('amount', 0))
            due_date = request.form.get('due_date')

            cursor.execute(
                "INSERT INTO bills (user_id, bill_name, amount, status, due_date) VALUES (%s, %s, %s, 'Unpaid', %s)",
                (user_id, bill_name, amount, due_date)
            )
            conn.commit()
            bill_id = cursor.lastrowid
            new_bill = {
                'bill_id': bill_id,
                'bill_name': bill_name,
                'amount': amount,
                'due_date': due_date,
                'status': 'Unpaid'
            }

        elif action == 'toggle':
            bill_id = int(request.form.get('bill_id'))
            new_status = request.form.get('status')

            cursor.execute(
                "UPDATE bills SET status=%s WHERE bill_id=%s AND user_id=%s",
                (new_status, bill_id, user_id)
            )
            conn.commit()

            new_bill = {
                'bill_id': bill_id,
                'status': new_status
            }

        elif action == 'edit':
            bill_id = int(request.form.get('bill_id'))
            bill_name = request.form.get('bill_name')
            amount = float(request.form.get('amount', 0))
            due_date = request.form.get('due_date')

            cursor.execute(
                "UPDATE bills SET bill_name=%s, amount=%s, due_date=%s WHERE bill_id=%s AND user_id=%s",
                (bill_name, amount, due_date, bill_id, user_id)
            )
            conn.commit()

            new_bill = {
                'bill_id': bill_id,
                'bill_name': bill_name,
                'amount': amount,
                'due_date': due_date
            }

        elif action == 'delete':
            bill_id = int(request.form.get('bill_id'))

            cursor.execute(
                "DELETE FROM bills WHERE bill_id=%s AND user_id=%s",
                (bill_id, user_id)
            )
            conn.commit()

            new_bill = {'bill_id': bill_id}

        # Recalculate totals
        cursor.execute(
            "SELECT amount, status FROM bills WHERE user_id=%s", (user_id,))
        bills = cursor.fetchall()
        total_bills = sum(float(b['amount']) for b in bills)
        total_paid = sum(float(b['amount'])
                         for b in bills if b['status'] == 'Paid')
        total_unpaid = total_bills - total_paid

        return jsonify({
            'success': True,
            'bill': new_bill,
            'total_bills': total_bills,
            'total_paid': total_paid,
            'total_unpaid': total_unpaid
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/update_split', methods=['POST'])
def update_split():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    split = int(request.form.get('split', 1))
    if split < 1:
        split = 1

    # Save in session
    session['split_among'] = split

    # Calculate your share dynamically for bill splitting
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT amount FROM bills WHERE user_id=%s", (user_id,))
    bills_data = cursor.fetchall()
    total_bills = sum(float(b['amount']) for b in bills_data)
    your_share = total_bills / split

    cursor.close()
    conn.close()

    return jsonify({
        'your_share': your_share,
        'split_among': split
    })


@app.route('/ipon', methods=['GET', 'POST'])
def ipon():
    user_id = session.get('user_id')
    if not user_id or session.get('role') == 'admin':
        return redirect(url_for('index'))
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True, buffered=True)

        # Fetch all bills
        cursor.execute(
            "SELECT amount, status FROM bills WHERE user_id=%s", (user_id,))
        bills = cursor.fetchall()
        total_bills = sum([float(b['amount']) for b in bills]) if bills else 0

        # Fetch split from session
        split_among = session.get('split_among', 1)
        your_share = total_bills / split_among if split_among else 0

        # Handle POST (only update if form submitted)
        daily_amount = request.form.get('daily_ipon')
        extra_amount = request.form.get('extra_amount')

        # Fetch or create ipon row for current month
        cursor.execute(
            "SELECT * FROM ipon WHERE user_id=%s AND month=%s", (user_id, current_month))
        ipon_row = cursor.fetchone()

        if ipon_row:
            if daily_amount:
                cursor.execute(
                    "UPDATE ipon SET saved_amount = saved_amount + %s WHERE user_id=%s AND month=%s",
                    (float(daily_amount), user_id, current_month)
                )
            if extra_amount:
                cursor.execute(
                    "UPDATE ipon SET goal_amount = goal_amount + %s WHERE user_id=%s AND month=%s",
                    (float(extra_amount), user_id, current_month)
                )
        else:
            saved = float(daily_amount) if daily_amount else 0
            goal_extra = float(extra_amount) if extra_amount else 0
            cursor.execute(
                "INSERT INTO ipon (user_id, saved_amount, goal_amount, month) VALUES (%s, %s, %s, %s)",
                (user_id, saved, goal_extra, current_month)
            )

        conn.commit()

        # Fetch the updated ipon row
        cursor.execute(
            "SELECT * FROM ipon WHERE user_id=%s AND month=%s", (user_id, current_month))
        ipon_data = cursor.fetchone()

        total_saved = int(ipon_data['saved_amount']) if ipon_data else 0
        extra_total = int(ipon_data['goal_amount']) if ipon_data else 0

        # Displayed for Goal
        goal = int(your_share + extra_total)
        remaining = max(goal - total_saved, 0)

        # Days left in month including today
        last_day = calendar.monthrange(current_year, current_month)[1]
        days_left = last_day - today.day + 1

        # Percentage for display
        percentage = round((total_saved / goal) * 100, 2) if goal > 0 else 0

    finally:
        cursor.close()
        conn.close()

    return render_template(
        'ipon.html',
        goal=goal,
        total_saved=total_saved,
        remaining=remaining,
        extra_total=extra_total,
        days_left=days_left,
        percentage=percentage
    )


@app.route('/history')
def history():
    user_id = session.get('user_id')
    if not user_id or session.get('role') == 'admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch only paid bills
    cursor.execute(
        "SELECT bill_name, amount, due_date FROM bills WHERE user_id=%s AND status='Paid' ORDER BY due_date DESC", (user_id,))
    paid_bills = cursor.fetchall()

    # Calculate summary
    total_paid_amount = sum(int(b['amount']) for b in paid_bills)
    total_paid_bills = len(paid_bills)
    last_payment_date = paid_bills[0]['due_date'] if paid_bills else None

    # Calculate "Last Payment" text
    if last_payment_date:
        from datetime import datetime
        today = datetime.now().date()
        last_date = last_payment_date if isinstance(
            last_payment_date, datetime) else datetime.strptime(str(last_payment_date), "%Y-%m-%d").date()
        days_ago = (today - last_date).days
        last_payment_text = f"{days_ago} days ago" if days_ago > 0 else "Today"
    else:
        last_payment_text = "No payments yet"

    cursor.close()
    conn.close()

    return render_template(
        'paymenthistory.html',
        paid_bills=paid_bills,
        total_paid_amount=total_paid_amount,
        total_paid_bills=total_paid_bills,
        last_payment_text=last_payment_text
    )


@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin':
        return "Access denied", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
    target_user = cursor.fetchone()

    if target_user and target_user['role'] == 'admin':
        flash("Cannot delete an admin user.", "error")
        return redirect(url_for('admin_dashboard'))

    # cursor.execute("DELETE FROM bills WHERE user_id = %s", (user_id,))
    # conn.commit()
    # cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    # conn.commit()

    try:
        cursor.execute("DELETE FROM ipon WHERE user_id = %s", (user_id,))
        cursor.execute(
            "DELETE FROM ipon_details WHERE user_id =%s", (user_id,))
        cursor.execute(
            "DELETE FROM payment_history WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM bills WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        cursor.execute("SELECT * FROM users ORDER BY user_id")
        users = cursor.fetchall()
        conn.commit()
        flash("User deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", "error")
        return render_template('admin.html')

    return render_template('admin.html', users=users, message="User deleted successfully.")


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
