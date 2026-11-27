# =============================================================================
# College Handbook  --  the only place the college text lives.
#
# Code node:  Language = Python (Native)      Mode = Run Once for All Items
#
# To change what the assistant knows, edit the text between the triple quotes
# below and run Stage 1 again. Nothing else in the workflow changes.
# Every "## " heading starts a new document, so keep the headings.
#
# No imports. n8n Cloud blocks every Python import, the standard library
# included, so this node uses plain string handling only.
# =============================================================================

HANDBOOK = """
# COLLEGE INFORMATION HANDBOOK — Geethanjali Institute of Science and Technology (GIST), Nellore

> SAMPLE TRAINING DATA. Every figure, name, date and rule in this handbook was written
> for a classroom exercise on Retrieval Augmented Generation. It is NOT the official
> handbook of any institution. Before any real use, replace each section below with the
> figures from your own college office, and keep the section headings as they are.

## 1. About the college

Geethanjali Institute of Science and Technology (GIST) is an engineering college at
Gangavaram village, Kovur mandal, on the Nellore to Bombay highway in SPSR Nellore
district, Andhra Pradesh. It was established in 2008 and is a co-educational,
non-minority institution offering undergraduate and postgraduate engineering
programmes.

The college is an autonomous institution affiliated to Jawaharlal Nehru Technological
University, Anantapur (JNTUA), approved by the All India Council for Technical
Education and recognised by the University Grants Commission. Degrees are awarded by
JNTUA; the college conducts its own examinations under its own academic regulations.
Admissions to the first year are made through the state counselling process. The
academic year runs from August to May and is divided into two semesters.

The campus sits on 24 acres and houses the academic blocks, central library, departmental
laboratories, two hostels, a sports ground, a canteen and the transport bay. The working
day for students is 9:20 a.m. to 4:20 p.m., Monday to Saturday, with the second and
fourth Saturday kept for departmental activities.

## 2. Programmes offered and sanctioned intake

The college offers four-year B.Tech programmes in five branches. Sanctioned intake per
branch for the current academic year:

- Computer Science & Engineering (CSE) — 180 seats
- Electronics & Communication Engineering (ECE) — 120 seats
- Electrical & Electronics Engineering (EEE) — 60 seats
- Mechanical Engineering (MECH) — 60 seats
- Civil Engineering (CIVIL) — 60 seats

Total sanctioned B.Tech intake is 480 seats. Of these, 70 per cent are filled through
convener quota by the state counselling authority and 30 per cent through management
quota by the college.

Two-year M.Tech programmes are offered in Computer Science & Engineering (18 seats) and
in Power Electronics (18 seats). Lateral entry into the second year of B.Tech is
available against 20 per cent supernumerary seats through the state ECET counselling for
diploma holders.

## 3. Admissions and registration for a fresh batch

Eligibility for first-year B.Tech is a pass in Intermediate (10+2) with Mathematics,
Physics and Chemistry, and a rank in the state engineering entrance examination (AP
EAPCET). Lateral entry candidates need a three-year diploma in a relevant branch and an
AP ECET rank.

Registration of a newly admitted student happens at the admission counter in the
administrative block and takes four steps:

1. Report with the allotment letter issued by the counselling authority and the original
   certificates for verification.
2. Pay the first-year fee at the accounts counter or by online transfer, and collect the
   fee receipt.
3. Fill the student registration form, the anti-ragging undertaking and the hostel or
   transport option form.
4. Collect the identity card, the academic calendar and the branch-wise section
   allotment from the department office.

Documents required at registration, originals with two photocopies each: AP EAPCET or
ECET rank card and hall ticket, allotment order, Intermediate or diploma marks
memorandum, Intermediate or diploma pass certificate, Secondary School Certificate for
date of birth, transfer certificate, study certificates for the last four years,
income certificate, caste certificate where applicable, Aadhaar card, and six passport
size photographs.

A newly admitted student is registered in the university within thirty days of joining,
after which the university issues the registered student number. Induction for the fresh
batch runs for one week before regular classes begin and covers the academic regulations,
the library and laboratory rules, the anti-ragging policy, the grievance mechanism and
the mentoring system. Each student is assigned a faculty mentor at induction.

Every continuing student also completes semester registration at the start of each
semester by paying the semester fee and confirming the subjects registered, including any
backlog subject being re-registered.

## 4. Fees structure

Annual tuition fee for B.Tech, convener quota, as notified by the state fee regulatory
authority: 48,000 rupees per year. For management quota the annual tuition fee is
85,000 rupees per year. Fees for the M.Tech programmes are 57,000 rupees per year.

Other charges, payable once per academic year:

- University registration and examination fee — 3,500 rupees
- Library and laboratory charges — 2,500 rupees
- Student activity and training fee — 2,000 rupees
- Identity card and insurance — 500 rupees

Hostel charges are 72,000 rupees per year, which covers accommodation and mess on a
twin-sharing basis. Transport is charged by route distance and ranges from 14,000 to
24,000 rupees per year. Both are optional and are collected only from students who opt
for them.

Fees may be paid in full at registration, or in two instalments: the first at
registration and the second before the start of the even semester. Payment is accepted by
online transfer, demand draft or at the accounts counter; cash above the limit notified by
the college is not accepted. A late payment carries a fee of 100 rupees per day of delay,
capped at 2,000 rupees per semester.

Students admitted under convener quota who qualify for state fee reimbursement pay only
the non-tuition charges at registration, and the tuition portion is adjusted when the
reimbursement is received. If a student withdraws, the refund follows the state
withdrawal rules: the full fee less a processing charge of 1,000 rupees is refunded when
the seat is vacated before the last date of admission, and no tuition refund is made
after that date.

## 5. Semester details and examinations

As an autonomous institution the college frames its own academic regulations and
conducts its own end-semester examinations; the degree is awarded by JNTUA. Students
admitted in different years may therefore sit under different regulations, and the
regulation code printed on the student's registration slip is the one that applies.

Each academic year has two semesters, odd and even, of about sixteen working weeks each.
A B.Tech programme has eight semesters and a total of 160 credits. Each semester carries
two mid-term examinations and one end-semester examination.

Internal marks carry 30 marks and the end-semester examination carries 70 marks, for a
total of 100 marks per subject. Internal marks are the better of the two mid-term scores
weighted at 80 per cent plus assignment and activity marks at 20 per cent. A student
passes a subject with 35 per cent in the end-semester examination and 40 per cent in
aggregate.

A minimum of 75 per cent attendance is required to be allowed into the end-semester
examination. Attendance between 65 and 75 per cent may be condoned once on medical
grounds, on application with supporting records, and on payment of the condonation fee.
Below 65 per cent the student is detained and repeats the semester with the next batch.

A student who fails a subject appears for it in the supplementary examination held after
the next end-semester examination. Revaluation of an end-semester answer script may be
applied for within fifteen days of the result, with the prescribed fee. The academic
calendar for each semester, with the mid-term and end-semester windows, is issued by the
examination branch at the start of the semester and displayed on the department notice
boards.

## 6. Scholarships and fee reimbursement

Students admitted through convener quota whose family income is within the limit notified
by the state government are eligible for post-matric fee reimbursement, applied for
through the state scholarship portal during the window announced each year. The
application needs the income certificate, caste certificate where applicable, the Aadhaar
number, and a bank account in the student's own name.

The college also awards merit scholarships from its own funds: a full tuition waiver to
students in the top ten state ranks who join the college, and a waiver of 25,000 rupees
per year to the branch topper of each semester. Sports scholarships are awarded to
students representing the university or the state.

## 7. Departments, heads and faculty

The college has five engineering departments and a department of Science and Humanities.
Faculty strength is 148, of whom 22 hold a doctorate. The student to teacher ratio is
maintained at 20 to 1.

Heads of department (sample names for this exercise):

- Computer Science & Engineering — Dr. P. Lakshmi Narayana, Professor, specialisation in
  machine learning and data engineering
- Electronics & Communication Engineering — Dr. S. Venkata Ramana, Professor,
  specialisation in VLSI design and embedded systems
- Electrical & Electronics Engineering — Dr. B. Suresh Babu, Professor, specialisation in
  power systems
- Mechanical Engineering — Dr. T. Anil Kumar, Professor, specialisation in thermal
  engineering
- Civil Engineering — Dr. G. Madhavi Latha, Professor, specialisation in structural
  engineering
- Science and Humanities — Dr. K. Rajeswari, Professor of Mathematics

Senior faculty in Computer Science & Engineering include Dr. M. Srinivasa Rao, Associate
Professor, working on natural language processing; Mrs. A. Haritha, Assistant Professor,
working on database systems; and Mr. V. Chandra Sekhar, Assistant Professor, working on
computer networks. Faculty counselling hours are from 3:30 p.m. to 4:20 p.m. on working
days, and each faculty mentor is responsible for about twenty students.

## 8. Facilities

The central library holds about 32,000 volumes across 4,200 titles, subscribes to the
national digital library consortium, and is open from 9 a.m. to 6 p.m. on working days
and 9 a.m. to 1 p.m. on Saturdays. A student may borrow two books at a time for fourteen
days; an overdue book carries a fine of one rupee per day.

Each department maintains its own laboratories. The Computer Science department has six
laboratories with 320 systems, a project laboratory and a dedicated server room, with a
campus internet bandwidth of 300 Mbps on a leased line.

Separate hostels for men and women accommodate 420 and 260 students respectively, with a
warden resident in each block. Hostel gates close at 7 p.m. and the study hour is 7:30
p.m. to 9:30 p.m. Thirteen buses operate on routes covering Nellore city, Kovur,
Podalakur, Venkatachalam, Buchireddypalem, Kavali and Gudur.

The campus has a sports ground for cricket and football, outdoor courts for volleyball,
basketball and kabaddi, an indoor hall for table tennis and carrom, a gymnasium, a
canteen, a stationery and reprographics counter, a health centre with a visiting medical
officer, and an ATM.

## 9. Training and placement

The training and placement cell runs communication and aptitude training from the second
year and technical training in the third year, and conducts mock interviews before the
placement season. Students become eligible for campus placement in the seventh semester,
subject to the eligibility criteria set by each visiting company.

The cell also arranges summer internships after the sixth semester, industry visits for
each branch once a year, and certification programmes in areas such as cloud computing,
data analytics and embedded systems through industry tie-ups.

## 10. Rules and code of conduct

Attendance is counted subject-wise and displayed every month. Leave of absence is applied
for in advance through the faculty mentor, and medical leave requires a certificate
submitted within a week of returning.

Ragging in any form is an offence under the regulations of the regulatory council and
attracts suspension and a report to the police. The anti-ragging committee and squad are
notified at the start of each year, and complaints may be made to any member, to the
principal, or to the national anti-ragging helpline.

Students wear the prescribed dress on working days and carry the identity card inside the
campus. Mobile phones are not used in the classrooms and laboratories. Misuse of
laboratory equipment, damage to property and malpractice in examinations are dealt with
by the disciplinary committee.

A grievance may be submitted in writing to the faculty mentor, the head of department or
the grievance redressal committee, and the committee responds within seven working days.
The internal complaints committee handles complaints of harassment.

## 11. Contacts and office hours

The administrative office is open from 9 a.m. to 5 p.m. on working days and from 9 a.m.
to 1 p.m. on Saturdays. The admission counter remains open during the counselling season
until 6 p.m.

For admissions and registration, contact the admission office. For fees, receipts and
reimbursement, contact the accounts section. For examinations, results, revaluation and
certificates, contact the examination branch. For hostel and transport, contact the
respective in-charge. The college website carries the current notifications, the academic
calendar and the circular archive.
"""

# cut the text into blocks, one per "## " heading
blocks = []
current = []
for line in HANDBOOK.strip().split("\n"):
    if line.startswith("## ") and current:
        blocks.append(current)
        current = []
    current.append(line)
if current:
    blocks.append(current)

out = []
for block in blocks:
    heading = block[0].lstrip("# ").strip()
    body = "\n".join(block[1:]).strip()
    if body == "":
        continue
    # the heading is repeated inside the text so every chunk says what it covers
    out.append({
        "json": {
            "section": heading,
            "text": heading + "\n\n" + body,
        }
    })

return out
