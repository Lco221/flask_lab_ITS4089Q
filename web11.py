import os

from flask import Flask, abort, redirect, render_template, request, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'development-key-change-me')

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'imdb_db')
mysql = MySQL(app)

@app.route('/')
def home():
    query = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'newest')
    sort_columns = {
        'newest': 'id DESC',
        'title_asc': 'title ASC',
        'title_desc': 'title DESC',
    }
    if sort not in sort_columns:
        sort = 'newest'

    cursor = mysql.connection.cursor()
    sql = 'SELECT id, title, description, image_url FROM movies'
    parameters = ()
    if query:
        sql += ' WHERE title LIKE %s OR description LIKE %s'
        search_term = f'%{query}%'
        parameters = (search_term, search_term)
    sql += f" ORDER BY {sort_columns[sort]}"
    cursor.execute(sql, parameters)
    movies = cursor.fetchall()
    cursor.close()
    return render_template('home.html', movies=movies, query=query, sort=sort)

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, title, description, image_url FROM movies WHERE id = %s", [movie_id])
    movie = cursor.fetchone()
    if movie is None:
        cursor.close()
        abort(404)

    cursor.execute("SELECT content, created_at FROM reviews WHERE movie_id = %s ORDER BY created_at DESC", [movie_id])
    reviews = cursor.fetchall()
    cursor.close()
    return render_template('detail.html', movie=movie, reviews=reviews)

@app.route('/movie/<int:movie_id>/review', methods=['POST'])
def add_review(movie_id):
    content = request.form.get('content', '').strip()
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id FROM movies WHERE id = %s', [movie_id])
    if cursor.fetchone() is None:
        cursor.close()
        abort(404)
    if content:
        cursor.execute(
            'INSERT INTO reviews (movie_id, content) VALUES (%s, %s)',
            (movie_id, content),
        )
        mysql.connection.commit()
    cursor.close()
    return redirect(url_for('movie_detail', movie_id=movie_id))

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', '5000')),
        debug=os.environ.get('FLASK_DEBUG') == '1',
    )
