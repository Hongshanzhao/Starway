import pandas as pd
# use relative path within backend folder
df_folder = os.path.join(os.getcwd(), 'backend')
xls = os.path.join(df_folder, '20260226105856_457.xls')
xl = pd.ExcelFile(xls)
print(xl.sheet_names)
for sheet in xl.sheet_names:
    df = pd.read_excel(xl, sheet_name=sheet)
    print(sheet)
    print(df.head())
    print(df.dtypes)
