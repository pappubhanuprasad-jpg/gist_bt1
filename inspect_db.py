import sqlite3
c = sqlite3.connect('sms.db')
tables = [r[0] for r in c.execute("select name from sqlite_master where type='table'").fetchall()]
print('tables:', tables)
for t in ('departments', 'registrations', 'users', 'students'):
    if t in tables:
        print(t, c.execute(f'select count(*) from {t}').fetchone()[0])
if 'departments' in tables:
    for r in c.execute('select id, code, name from departments').fetchall():
        print('dept', r)
if 'registrations' in tables:
    cols = [d[1] for d in c.execute('pragma table_info(registrations)').fetchall()]
    print('reg cols:', cols)
    for r in c.execute('select id, reference_no, full_name, status from registrations').fetchall():
        print('reg', r)
