from flask import Flask, url_for, render_template, request, redirect
import csv
import json
app = Flask(__name__)


@app.route('/')
def hello():
    urls = {'главная страница': url_for('hello'),
            'спасибо': url_for('thank'),
            'статистика': url_for('stats'),
            'вывод данных': url_for('json'),
            'поиск': url_for('search'),
            'результаты поиска': url_for('results'),}
    return render_template('hello.html', urls=urls)


@app.route('/', methods = ['POST', 'GET'])
def form():
    if request.method == 'POST':
        sex = request.form['sex']
        age = request.form['age']
        birth = request.form['birth']
        place = request.form['place']
        multi = request.form['multi']
        burak = request.form['burak']
        veho = request.form['veho']
        lent = request.form['lent']
        fieldnames = ['sex', 'age', 'birth', 'place', 'multi', 'burak', 'veho', 'lent']
        with open('answers.csv', 'a+', encoding = 'utf-8') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames, delimiter = '\t')
            writer.writerow({'Пол': sex, 'Возраст': age, 'Место рождения': birth, 'Местожительство': place,
                'Мультифора': multi, 'Свекла': burak, 'Мочалка': veho, 'Швабра': lent })
        return render_template('hello.html')
    return redirect(url_for('thank'))

@app.route('/thank', methods = ['POST', 'GET'])
def thank():
    return render_template('thank')

@app.route('/stats')
def stats():
    return render_template('stats.html')

 
@app.route('/json')
def json():
    return render_template('json.html')

@app.route('/search')
def search():
    return render_template('search.html')


@app.route('/results')
def results():
    return render_template('results.html')


if __name__ == '__main__':
    app.run(debug=False)
