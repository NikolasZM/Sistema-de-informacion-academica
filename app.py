from flask import Flask, jsonify, request, render_template
import pymysql

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')
