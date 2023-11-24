import os
import pandas as pd

def read_and_filter_data(file_path='city_payroll_data.csv', cached_file='./data/teachers_payroll.csv'):
    '''
    
    '''
    # Check for teachers payroll data
    if os.path.exists(cached_file):
        return pd.read_csv(cached_file)
    # Load the city payroll
    else:
        data = pd.read_csv(file_path)

        conditions = (
            (data['Agency Name'] == 'DEPT OF ED PEDAGOGICAL') &
            (data['Title Description'] == 'TEACHER') &
            # (data['Leave Status as of June 30'] == 'ACTIVE') &
            (data['Regular Gross Paid'] > 0)
        )

        # Drop unused columns
        df = data[conditions].drop(columns=['Payroll Number', 'Agency Name', 'Work Location Borough',
                                        'Title Description', 'Pay Basis', 'Regular Hours', 'OT Hours',
                                        'Total OT Paid', 'Leave Status as of June 30']).drop_duplicates()

        df.rename(columns={'Agency Start Date': 'Hire Date',
                           'Base Salary': 'Salary'}, inplace=True)

        # Cast Hire Date to datetime and add Hire Year
        df['Hire Date'] = pd.to_datetime(df['Hire Date'], errors='coerce')
        df = df.dropna(subset=['Hire Date'])
        df['Hire Year'] = df['Hire Date'].dt.year
        df['Hire Year'] = df['Hire Year'].astype('Int16')

        # Calculate the number of years employed as a NYC teacher
        df['Years of Employment'] = df['Fiscal Year'] - df['Hire Year']
        df['Years of Employment'] = df['Years of Employment'].astype('Int16')
        df['Years of Employment'] = pd.to_numeric(df['Years of Employment'], errors='coerce')

        # Calculate teachers total gross pay
        df['Total Paid'] = df['Regular Gross Paid'] + df['Total Other Pay']

        df = df.dropna(subset=['Years of Employment'])

        # Employee Key
        df[['Last Name', 'First Name', 'Mid Init']] = df[['Last Name', 'First Name', 'Mid Init']].apply(
            lambda x: x.str.strip().str.title().fillna('None')
        )
        df['FirstMidLastStart'] = df['First Name'] + df['Mid Init'] + df['Last Name'] + df['Hire Date'].astype(str)

        df = df.sort_values(by='Fiscal Year').reset_index(drop=True)

        # Salary changes YoY
        df['Salary Delta'] = df.groupby(['FirstMidLastStart'])['Salary'].pct_change() * 100
        df['Salary Monetary Diff'] = df.groupby(['FirstMidLastStart'])['Salary'].diff()

        df['Total Paid Delta'] = df.groupby(['FirstMidLastStart'])['Total Paid'].pct_change() * 100
        df['Total Paid Monetary Diff'] = df.groupby(['FirstMidLastStart'])['Total Paid'].diff()
        
        df[['Salary Delta',
            'Salary Monetary Diff',
            'Total Paid Delta',
            'Total Paid Monetary Diff']] = (df[['Salary Delta',
                                                'Salary Monetary Diff',
                                                'Total Paid Delta',
                                                'Total Paid Monetary Diff']]
                                            .fillna(0)
                                            .round(2)
                                            )

        ## Categorical Features
        employment_bins = [-1, 5, 10, 15, 20, 25, 30, 35, 40, 50]
        employment_labels = ['0-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31-35', '36-40', '41+']

        # Define bin edges for 'Salary'
        salary_bins = [40000, 60000, 80000, 100000, 120000, 140000, 160000]
        salary_labels = ['40k-60k', '60k-80k', '80k-100k', '100k-120k', '120k-140k', '140k-160k+']

        # Define bin edges for 'Salary Delta'
        delta_bins = [-50, 0, 5, 10, 15, 20, 30, 40, 50, 100, 200]
        delta_labels = ['<-5%', '0-5%', '5-10%', '10-15%', '15-20%', '20-30%', '30-40%', '40-50%', '50-100%', '100%+']

        # Define bin edges for 'Salary Monetary Diff'
        monetary_diff_bins = [-60000, -5000, 5000, 10000, 15000, 20000, 30000, 40000, 50000, 60000, 70000]
        monetary_diff_labels = ['<-5k', '-5k-5k', '5k-10k', '10k-15k', '15k-20k', '20k-30k', '30k-40k', '40k-50k', '50k-60k', '60k+']

        # Apply binning to create categorical features
        df['Employment Category'] = pd.cut(df['Years of Employment'], bins=employment_bins, labels=employment_labels)
        df['Salary Category'] = pd.cut(df['Salary'], bins=salary_bins, labels=salary_labels)
        df['Salary Delta Category'] = pd.cut(df['Salary Delta'], bins=delta_bins, labels=delta_labels)
        df['Salary Monetary Diff Category'] = pd.cut(df['Salary Monetary Diff'], bins=monetary_diff_bins, labels=monetary_diff_labels)
        df['Total Paid Category'] = pd.cut(df['Total Paid'], bins=salary_bins, labels=salary_labels)
        df['Total Paid Delta Category'] = pd.cut(df['Total Paid Delta'], bins=delta_bins, labels=delta_labels)
        df['Total Paid Monetary Diff Category'] = pd.cut(df['Total Paid Monetary Diff'], bins=monetary_diff_bins, labels=monetary_diff_labels)

        # Transform bins into categorical features
        df['Employment Category'] = pd.Categorical(df['Employment Category'],categories=employment_labels,ordered=True)
        df['Salary Category'] = pd.Categorical(df['Salary Category'],categories=salary_labels,ordered=True)
        df['Salary Delta Category'] = pd.Categorical(df['Salary Delta Category'],categories=delta_labels,ordered=True)
        df['Salary Monetary Diff Category'] =  pd.Categorical(df['Salary Monetary Diff Category'],categories=monetary_diff_labels,ordered=True)
        df['Total Paid Category'] = pd.Categorical(df['Total Paid Category'],categories=salary_labels,ordered=True)
        df['Total Paid Delta Category'] = pd.Categorical(df['Total Paid Delta Category'],categories=delta_labels,ordered=True)
        df['Total Paid Monetary Diff Category'] = pd.Categorical(df['Total Paid Monetary Diff Category'],categories=monetary_diff_labels,ordered=True)


        # Drop unused columns and reorder columns
        df = df.drop(columns=['Last Name', 'First Name', 'Mid Init'])

        # Remove outliers
        df = df[(df['Hire Year']>=1980)&
                (df['Years of Employment']<=50)&
                (df['Fiscal Year']>2014)]

        df = df[['Fiscal Year', 'Hire Date', 'Hire Year', 'Years of Employment',
                 'FirstMidLastStart', 'Salary', 'Total Other Pay', 'Total Paid',
                 'Employment Category',
                 'Salary Category',
                 'Total Paid Category',
                 'Salary Delta Category',
                 'Total Paid Delta Category',
                 'Salary Monetary Diff Category',
                 'Total Paid Monetary Diff Category',
                 'Salary Delta',
                 'Total Paid Delta',
                 'Salary Monetary Diff',
                 'Total Paid Monetary Diff']]
        
        # Save teachers payroll dataset
        df.to_csv('./data/teachers_payroll.csv', index=False)

        return df


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