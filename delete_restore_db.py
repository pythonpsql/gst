import os
import sys

f = sys.argv[1]
if os.path.exists(f):
    print(f)

    delete_command = "psql -U dba_tovak -d postgres -h localhost -c 'drop database gst_old'"

    print(delete_command)
    confirm_ = input("Do you want to execute the above command? (y/n)").strip().lower()
    if confirm_ == "y":
        os.system(delete_command)
        restore_command = "pg_restore -U dba_tovak -h localhost -C -d postgres " + f
        print(restore_command)
        confirm_ = input("Do you want to execute the above command? (y/n)").strip().lower()
        if confirm_ == "y":
            os.system(restore_command)
            print("db restored")
        else:
            print('You canceled. DB was no restored')
    else:
        print('You canceled. No changes were made')
else:
    print("You need to specify a valid file path to restore data from")
    print("e.g. python delete_restore_db.py <filepath>")

