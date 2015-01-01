def connect(sets):
    db = sets.get('db', None)

    if db is None:
        return None

    if db == 'sqlite' or db == 'sqlite3':
        db_table = sets.get('db_table', 'default.db')
        import sqlite3
        return sqlite3.connect(db_table)

    return None

def create(db, table, items):
    items_str = ','.join(items)

    c = db.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS %s (%s)' % (table, items_str))

    db.commit()

def select(db, table, items='', where=''):
    items_str = ','.join(["%s" % x for x in items])
    if not items_str:
        items_str = '*'

    c = db.cursor()
    if where:
        print('SELECT %s from %s WHERE %s' % (items_str, table, where))
        c.execute('SELECT %s from %s WHERE %s' % (items_str, table, where))
    else:
        print('SELECT %s from %s' % (items_str, table))
        c.execute('SELECT %s from %s' % (items_str, table))

    return c.fetchall()

def insert(db, table, items):
    items_str = ','.join(["'%s'" % x for x in items])

    c = db.cursor()
    c.execute('INSERT INTO %s VALUES (%s)' % (table, items_str))

    db.commit()

def delete(db, table, where):
    c = db.cursor()
    c.execute('DELETE FROM %s WHERE %s' % (table, where))

    db.commit()
