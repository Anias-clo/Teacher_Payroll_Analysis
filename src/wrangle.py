import pandas as pd

def main():
    '''
    
    '''
    # Load NYC Payroll data
    data = pd.read_csv('city_payroll_data.csv')

    # Filter data for 'DEPT OF ED PEDAGOGICAL' agency and 'TEACHER' title
    df = data[(data['Agency Name'] == 'DEPT OF ED PEDAGOGICAL')&
              (data['Title Description'] == 'TEACHER')&
              (data['Fiscal Year']>=2020)]

    # Drop unused columns
    df = df.drop(columns=['Payroll Number', 'Agency Name',
                            'Title Description', 'Pay Basis',
                            'Regular Hours', 'OT Hours'])

    df.rename(columns={'Leave Status as of June 30':'Leave Status',
                    'Agency Start Date': 'Hire Date'}, inplace=True)

    # Sort and reset index
    df = df.sort_values(by='Fiscal Year')
    df = df.reset_index(drop=True)

    # Convert 'Hire Date' to datetime, add 'Hire Year' and 'Years of Employment'
    df['Hire Date'] = pd.to_datetime(df['Hire Date'], errors='coerce')
    # Filter out rows with NaT values
    valid_dates = df['Hire Date'].notna()
    # Use the .dt accessor on valid dates
    df.loc[valid_dates, 'Hire Year'] = df.loc[valid_dates, 'Hire Date'].dt.year
    # Convert Years from float to int
    df['Hire Year'] = df['Hire Year'].astype('Int16')
    df['Years of Employment'] = df['Fiscal Year'] - df['Hire Year']
    df['Years of Employment'] = df['Years of Employment'].astype('Int16')

    # Normalize strings
    df['Work Location Borough'] = df['Work Location Borough'].str.strip().str.title()
    df['Last Name'] = df['Last Name'].str.strip().str.title()
    df['First Name'] = df['First Name'].str.strip().str.title()
    df['Leave Status'] = df['Leave Status'].str.strip().str.title()
    # Fill in Missing Middle Initial
    df['Mid Init'] = df['Mid Init'].fillna('None')

    # Concatenated Key
    df['FirstMidLastStart'] = df['First Name'] + df['Mid Init'] + df['Last Name'] + df['Hire Date'].astype(str)

    # Calculate 'Total Pay' and save to CSV
    df['Total Pay'] = df['Regular Gross Paid'] + df['Total Other Pay']
    
    df.to_csv('teachers_payroll.csv', index=False)

if __name__ == "__main__":
    main()


############# Future Analysis ####################
# All education related agencies
education_agencies = [
'DEPT OF ED PER DIEM TEACHERS',
'DEPT OF ED PER SESSION TEACHER',
'DEPARTMENT OF EDUCATION ADMIN',
'DEPT OF ED HRLY SUPPORT STAFF',
'DEPT OF ED PARA PROFESSIONALS',
'DEPT OF ED PEDAGOGICAL',
'TEACHERS RETIREMENT SYSTEM',
'NYC EMPLOYEES RETIREMENT SYS'
]