import pandas as pd
import numpy as np

# change the way numbers displayed
pd.options.display.float_format = 'ILS {:,.2f}'.format

def print_groups(groupobject):
    for name, group in groupobject:
        print(name)
        print(group.head())

xl = pd.ExcelFile("Portfolio.xlsx")
xl.sheet_names
df = xl.parse("Portfolio")
df.head()
#print(df.head())

# rename some columns
df=df.rename(columns = {'Current\nValue [ILS]':'Value'})

# select out only the columns we are interested in (and place in the order we need)
df = df[['Account', 'Symbol', 'Name', 'Major Asset Class', 'Minor Asset 1', 'Minor Asset 2', 'Minor Asset 3', 'Minor Asset 4', 'Value']]

def by_account(df):
    a = df.groupby(by=['Account']).sum()
    total = a.sum()
    b = a / total
    a['Percentage'] = b

    output = a.to_string(formatters={
        'Value': 'ILS {:,.2f}'.format,
        'Percentage': '{:,.2%}'.format
    })
    print(output)

def by_assetclass(df):
    for level in range(0,4):
        a=df.groupby(by=['Account', 'Major Asset Class', 'Minor Asset 1', 'Minor Asset 2', 'Minor Asset 3', 'Minor Asset 4']).sum().groupby(level=[level]).sum()
        print(a)
        total = a.sum()
        b=a/total

        a['Percentage'] = b

        output = a.to_string(formatters={
            'Value': 'ILS {:,.2f}'.format,
            'Percentage': '{:,.2%}'.format
        })
        print(output)

# by_account(df)
# by_assetclass(df)
#
# a = df.groupby(by=['Account', 'Major Asset Class', 'Minor Asset 1', 'Minor Asset 2', 'Minor Asset 3',
#                    'Minor Asset 4']).sum()
#
# b = a / a.sum()
#
# a['Percentage'] = b
#
# output = a.to_string(formatters={
#     'Value': 'ILS {:,.2f}'.format,
#     'Percentage': '{:,.2%}'.format
# })
# print(output)

########################################
def analyze_account(name, df):
    print('\n\n\n' + name)
    accounts = df.groupby(by=['Account'])

    account = accounts.get_group(name)
    # a = account.groupby(by=['Major Asset Class', 'Minor Asset 1', 'Minor Asset 2', 'Minor Asset 3',
    #                    'Minor Asset 4']).sum()
    a = account.groupby(by=['Minor Asset 1', 'Major Asset Class']).sum()

    b = a / a.sum()

    a['Percentage'] = b

    output = a.to_string(formatters={
        'Value': 'ILS {:,.2f}'.format,
        'Percentage': '{:,.2%}'.format
    })
    print(output)
    print('Total Value: ', account['Value'].sum())

# analyze all accounts
accounts = df.groupby(by=['Account'])
for account in accounts.groups:
    print(account)
    analyze_account(account, df)

print('#############################################################')
# table = pd.pivot_table(df, values=['Value'],
#                        index=['Major Asset Class'], columns=['Account'], aggfunc=np.sum, margins=True, dropna=True,fill_value=0).stack('Account')
# print(table)

table = pd.pivot_table(df, index=['Major Asset Class', 'Minor Asset 1', 'Minor Asset 2', 'Minor Asset 3'],aggfunc=np.sum, margins=True, dropna=True,fill_value=0)
table['% of Total'] = (table.Value / table.Value.sum() * 100)
print(table)

table = pd.pivot_table(df, index=['Major Asset Class', 'Minor Asset 1'],aggfunc=np.sum, margins=True, dropna=True,fill_value=0)
table['% of Total'] = (table.Value / table.Value.sum() * 100)
table['%Major'] = (table.Value / table.groupby(level=0).Value.transform(sum) * 100)
print(table)



#table['%Major'] = (table.Value / table.groupby(level=0).Value.transform(sum) * 100)
#table['%Minor1'] = (table.Value / table.groupby(level=2).Value.transform(sum) * 100)
#table.loc['total', :] = table.sum().values
#print(table)

print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
table = pd.pivot_table(df,
                       index=['Account','Major Asset Class', 'Minor Asset 1', 'Minor Asset 2', 'Minor Asset 3', 'Minor Asset 4', 'Name'],
                       values=['Value'],
                       aggfunc=np.sum, margins=True, dropna=True,fill_value=0)
table = table.query('Account == ["IRA-Orna"]')
g = table.groupby(level=['Major Asset Class']).sum()
g.index = [g.index, ['Total'] * len(g)]
print(g)
h = pd.concat([table,g]).sort_index()
print(h)

table = pd.pivot_table(df, values=['Value'],
                       columns=['Account'],
                       index=['Major Asset Class','Minor Asset 1', 'Minor Asset 2','Minor Asset 3', 'Minor Asset 4'],
                       fill_value=0, aggfunc=np.sum, dropna=True, margins=True)
print(table)
t=table.to_html('test.html')

tab_tots = table.groupby(level='Major Asset Class').sum()
print(tab_tots)
t=pd.concat(
    [table, tab_tots]
)
t.to_html('test.html')

## https://stackoverflow.com/questions/43238183/python-pandas-add-subtotal-on-each-lvl-of-multiindex-dataframe
L=['Major Asset Class', 'Minor Asset 1', 'Minor Asset 2', 'Minor Asset 3', 'Minor Asset 4']
t=pd.concat([
        df.assign(
            **{x: 'Total' for x in L[i:]}
        ).groupby(L).sum() for i in range(5)
    ]).sort_index()
t.to_html('test.html')

