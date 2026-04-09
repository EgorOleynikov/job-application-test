sqlite3_db_path = "db"
table_name = "hierarhy"

def colour_scheme(state: int):
    match state:
        case 0:
            return 'OrangeRed'
        case 1:
            return 'LemonChiffon'
        case 2:
            return 'LightGreen'
        case 3:
            return 'LightSkyBlue'
        case _:
            return 'White'
