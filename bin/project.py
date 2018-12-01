from flask import Flask, url_for, render_template, request, redirect
import csv
import json
app = Flask(__name__)


@app.route('/')
def hello():
    urls = {'главная страница': url_for('hello'),
            'анкета': url_for('initial'),
            'спасибо за ответ!': url_for('thank'),
            'статистика': url_for('stats'),
            'вывод данных': url_for('json'),
            'поиск': url_for('search'),
            'результаты поиска': url_for('results'),}
    #ans = request.args['name']
    #with open('answers.csv', 'a', encoding = 'utf-8') as f:
        #writer = csv.DictWriter(f, fieldnames = fieldnames, delimiter = '\t')
    return render_template('hello.html', urls=urls)

@app.route('/initial', methods = ['GET', 'POST'])
def initial():
    if request.args:
        sex = request.args['sex']
        age = request.args['age']
        birth = request.args['birth']
        place = request.args['place']
        multi = request.args['multi']
        burak = request.args['burak']
        veho = request.args['veho']
        lent = request.args['lent']
        fieldnames = ['sex', 'age', 'birth', 'place', 'multi', 'burak', 'veho', 'lent']
        with open('answers.csv', 'a+', encoding = 'utf-8') as f:
            writer = csv.DictWriter(f, fieldnames = fieldnames, delimiter = '\t')
            writer.writerow({'Пол': sex, 'Возраст': age, 'Место рождения': birth, 'Местожительство': place,
                'Мультифора': multi, 'Свекла': burak, 'Мочалка': veho, 'Швабра': lent })
        return render_template('thank.html')
        #return render_template('thank.html')
    return redirect(url_for('initial'))

@app.route('/thank', methods = ['GET', 'POST'])
def thank():
    return render_template('thank.html')
    
@app.route('/stats')
def stats():
    return '<p>Hello</p>'

 
@app.route('/json')
def json():
    #with open('res.json', 'w') as f:
        #json.dump(request.form, f)
    #return render_html('answers.html')
    return '<p>Hello</p>'

@app.route('/search')
def search():
    return '<p>Hello</p>'


@app.route('/results')
def results():
    return '<p>Hello</p>'


if __name__ == '__main__':
    app.run(debug=False)
