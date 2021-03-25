from flask import Flask, render_template, request, redirect, url_for
import csv, os

# this is to read info from "subjects.csv"
def read_info():
    # the following two lines of codes will tell us the abs path (from root to the directory) of the file
    curr_dir = os.path.dirname(os.path.abspath(__file__))   # getting abs path for current file
    file_name = os.path.join(curr_dir, "static/subjects.csv")
    with open(file_name, "r") as f:
        csvreader = csv.reader(f)
        header = next(csvreader)   # remove header line
        rows = []
        for row in csvreader:
            rows.append(list(row))
    return rows

subj_info = read_info()

def score_to_gpa_grade(score):
    conversion_table = {
        85: (5.0, '1*'),
        75: (4.0, 'A1'),
        70: (3.5, 'A2'),
        65: (3.0, 'B3'),
        60: (2.5, 'B4'),
        55: (2.0, 'C5'),
        50: (1.5, 'C6'),
        45: (1.0, 'D7'),
        40: (0.5, 'E8'),
        0: (0.0, 'F9'),
    }

    for key in conversion_table:
        if score >= key:
            return conversion_table[key]

def gpa_norm(all_subjs):
    total = 0
    weightage = 0
    for subj in all_subjs:
        if  subj[1] == 'ss':
            total += subj[7] * 0.5
            weightage += 0.5
        else:
            total += subj[7]
            weightage += 1
    return round(total/weightage, 2)

def gpa_sec4(all_subjs):
    # assume GPA is calculated using: 
    # 2 lang
    # math
    # cid
    # ss (0.5)
    # one best sci
    # one best hum
    # one best others
    best_sci = ['subj', 0]
    best_hum = ['subj', 0]
    best_other = ['subj', 0]

    # find best sci and best hum first
    for subj in all_subjs:
        if subj[2] == 'Science' and subj[5] > best_sci[1]:
            best_sci = [subj[1], subj[5]]
        elif subj[2] == 'Humanities' and subj[5] > best_hum[1] and subj[1] != 'ss':
            best_hum = [subj[1], subj[5]]
    # print(all_subjs)
    # print(best_sci)
    # print(best_hum)

    # find best other
    for subj in all_subjs:
        if subj[2] in ['Science', 'Humanities', 'Maths'] and\
            subj[1] != best_sci[0] and subj[1] != best_hum[0] and subj[1] != 'ss':
            # this one means, is one of the sci/hum/math, but not the best sci/hum and not ss
            if subj[5] > best_other[1]:
                best_other = [subj[1], subj[5]]
    # print(best_other)

    # calc gpa and indicate if counted or double-counted
    total_gpa = 0
    total_weight = 0
    for subj in all_subjs:
        if subj[4] == 'T':
            # caters for all compul subj
            if subj[1] =='ss':
                total_gpa += subj[7] * 0.5
                total_weight += 0.5
            else:
                total_gpa += subj[7]
                total_weight += 1
            subj.append('C')

        if subj[1] == best_sci[0]\
        or subj[1] == best_hum[0]\
        or subj[1] == best_other[0]:
            total_gpa += subj[7]
            total_weight += 1
            if subj[1] == 'maths':
                subj[-1] = 'D'
            else:
                subj.append('C')
    for subj in all_subjs:
        if subj[-1] not in ["C", "D"]:
            subj.append('U')

    gpa = round(total_gpa/total_weight, 2)
    return gpa

app = Flask(__name__)
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/subjpage/")
def subjpage():
    lvl = request.args['lvl']
    if lvl in "12":
        # if sec 1 or 2, no need select optional subjects
        return redirect(url_for('process_res', lvl=lvl))
    # if sec 3 or 4, select optional subjects

    compul_subj = []
    opt_sci_subj = []
    opt_hum_subj = []

    # for subj in subj_info:
    #     if lvl in subj[3] and row[4] == 'T':
    #         compul_subj.append(subj)
    #     elif...

    compul_subj = [subj for subj in subj_info if lvl in subj[3] and subj[4] == "T"]
    opt_sci_subj = [subj for subj in subj_info if lvl in subj[3] and subj[4] == "F" and subj[2]=='Science']
    opt_hum_subj = [subj for subj in subj_info if lvl in subj[3] and subj[4] == "F" and subj[2]=='Humanities']
    # print(compul_subj)
    # print(opt_hum_subj)
    # print(opt_sci_subj)

    return render_template("subjPage.html", lvl=lvl, compul_subj=compul_subj, opt_hum_subj=opt_hum_subj, opt_sci_subj=opt_sci_subj)

@app.route('/process/', methods=["POST", "GET"])
def process_res():
    if request.method == "GET":
        # GET request, render page 3 (score)
        lvl = request.args['lvl']
        all_subjs = []
        if lvl in "12":
            # sec 1/2, only have compul_subj
            for row in subj_info:
                if lvl in row[3]:
                    all_subjs.append(row)
        else:
            # sec3/4, read opt_subjs
            # print(request.args)
            sci_subjs = request.args.getlist('opt_sci_subj')
            hum_subjs = request.args.getlist('opt_hum_subj')
            # print(sci_subjs)
            # print(hum_subjs)
            for row in subj_info:
                if lvl in row[3] and row[4] == 'T':
                    # compul_subj
                    all_subjs.append(row)
                elif row[1] in sci_subjs or row[1] in hum_subjs:
                    # selected opt_subj
                    all_subjs.append(row)
            # print(all_subjs)

        return render_template("score.html", lvl=lvl, all_subjs=all_subjs)
    else:
        # POST request, render page 4 (results)
        lvl = request.form['lvl']
        all_subjs = []
        for key in request.form:
            if key != "lvl":
                # if this is a subj:
                # look thru all subj_info to find the relevant row of this subj
                for row in subj_info:
                    if row[1] == key:
                        # "row.copy()" will create a duplicate list without changing the original 
                        new_row = row.copy()
                        score = int(request.form[key])
                        # print(score)
                        gpa, grade = score_to_gpa_grade(score)
                        new_row.append(score)
                        new_row.append(grade)
                        new_row.append(gpa)
                        all_subjs.append(new_row)
                        break   # there is exactly 1 match, can break after found
        # print(score_to_gpa_grade(all_subjs))
        # print(all_subjs)
        if lvl != '4':
            gpa = gpa_norm(all_subjs)
        else:
            gpa = gpa_sec4(all_subjs)
        return render_template('result.html', lvl=lvl, gpa=gpa, all_subjs=all_subjs)

if __name__ == "__main__":
    app.run(debug=True)