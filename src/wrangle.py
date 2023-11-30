import os
import numpy as np
import pandas as pd


def read_teacher_data(cached_file='./data/teachers_payroll.csv'):
    '''
    Reads and returns the NYC teachers payroll data from a CSV file.
    
    Parameters:
    - cached_file (str): Path to the cached CSV file containing teachers payroll data.
    
    Returns:
    - pd.DataFrame: DataFrame containing NYC teachers payroll data.
    '''
    df = pd.read_csv(cached_file, engine='pyarrow')

    df['Hire Date'] = pd.to_datetime(df['Hire Date'])
    df['Salary'] = df['Salary'].astype('int')
    df['Hire Year'] = df['Hire Year'].astype('Int16')
    df['Hire Month'] = df['Hire Month'].astype('Int16')
    df['Years of Employment'] = df['Years of Employment'].astype('Int16')
    df['Employee ID'] = df['Employee ID'].astype('O')

    employment_labels = ['0-5', '6-10', '11-15', '16-20', '21-25', '26+']
    salary_labels = ['40k-60k', '60k-80k', '80k-100k', '100k-120k', '120k-140k', '140k-160k+']
    additional_pay_labels = ['<$0', '$0', '0-$500', '$500-$1K', '$1k-$3K', '$3K-$10K', '$10K+']
    delta_labels = ['<=0%', '0.01-5%', '5-10%', '10-15%', '15+%']
    simplified_delta_labels = ['Salary Decreased', 'No Change', 'Salary Increased']
    monetary_diff_labels = ['<=0k','1-5k', '5k-10k', '10k-15k', '15k-20k', '20k+']

    # Pay schedule categories
    paystep_labels = ['Other','1A', '2A', '3A', '4A', '5A', '6A', '6A+L5', '6B', '6B+L5', '7A',
                        '7A+L5', '7B', '7B+L5', '8A', '8A+L5', '8B', '8B+L5', '8B+L10', '8B+L13',
                        '8B+L15', '8B+L18', '8B+L20', '8B+L22']
    differential_labels = ['Other','BA','Pre1970','BA+30','BA+60','BA+66','BA+96','MA','MA+']
    differential_category_labels = ['Other', 'Bachelor\'s Degree', 'Pre1970 Teacher',
                                    'Bachelor\'s Degree + 30 Credit Hours',
                                    'Bachelor\'s Degree + 60 Credit Hours',
                                    'Bachelor\'s Degree + 66 Credit Hours',
                                    'Bachelor\'s Degree + 96 Credit Hours',
                                    'Master\'s Degree', 'Master\'s Degree Plus']
    salary_schedule_labels = ['Other','2013', '2014 May', '2014 Sept', '2015',
                                '2016', '2017', '2018 May', '2018 June', '2019',
                                '2020', '2021', '2022', '2024']
    degree_labels = ['Other', 'Bachelor\'s', 'Master\'s']

    # Transform bins into categorical features
    df['Employment Category'] = pd.Categorical(df['Employment Category'], categories=employment_labels, ordered=True)
    df['Salary Category'] = pd.Categorical(df['Salary Category'], categories=salary_labels, ordered=True)
    df['Additional Pay Category'] = pd.Categorical(df['Additional Pay Category'],categories=additional_pay_labels,ordered=True)  
    df['Salary Delta Category'] = pd.Categorical(df['Salary Delta Category'], categories=delta_labels, ordered=True)
    df['Salary Simplified Delta Category'] = pd.Categorical(df['Salary Simplified Delta Category'],
                                                            categories=simplified_delta_labels, ordered=True)
    df['Salary Monetary Diff Category'] = pd.Categorical(df['Salary Monetary Diff Category'],
                                                         categories=monetary_diff_labels, ordered=True)
    
    df['Paystep'] = pd.Categorical(df['Paystep'], categories=paystep_labels , ordered=True)
    df['Differential'] = pd.Categorical(df['Differential'], categories=differential_labels , ordered=True)
    df['Differential Category'] = pd.Categorical(df['Differential Category'], categories= differential_category_labels, ordered=True)
    df['Salary Schedule'] = pd.Categorical(df['Salary Schedule'], categories=salary_schedule_labels , ordered=True)
    df['Degree'] = pd.Categorical(df['Degree'], categories=degree_labels, ordered=True)

    return df


def read_and_filter_data(file_path='city_payroll_data.csv', cached_file='./data/teachers_payroll.csv'):
    '''
    Reads, filters, and returns NYC teachers payroll data from a CSV file.
    If a cached file is available, it is used; otherwise, the data is loaded and processed.
    
    Parameters:
    - file_path (str): Path to the city payroll data CSV file.
    - cached_file (str): Path to the cached CSV file for teachers payroll data.
    
    Returns:
    - pd.DataFrame: DataFrame containing filtered and processed NYC teachers payroll data.
    '''
    # Check for teachers payroll data
    if os.path.exists(cached_file):
        return read_teacher_data(cached_file)
    # Load the city payroll
    else:
        data = pd.read_csv(file_path,engine='pyarrow')

        # Filter for teachers that haven't retired
        conditions = (
            (data['Agency Name']=='DEPT OF ED PEDAGOGICAL') &
            (data['Title Description']=='TEACHER') &
            (data['Leave Status as of June 30']!='CEASED') &
            (data['Regular Gross Paid']>0)
        )

        # Drop unused columns and remove duplicates
        df = data[conditions].drop(columns=['Payroll Number', 'Agency Name', 'Work Location Borough',
                                            'Title Description', 'Pay Basis', 'Regular Hours', 'OT Hours',
                                            'Total OT Paid', 'Leave Status as of June 30']
                                  ).drop_duplicates()

        # Rename columns
        df.rename(columns={'Agency Start Date': 'Hire Date',
                           'Base Salary': 'Salary',
                           'Total Other Pay': 'Additional Pay'}, inplace=True)

        # Cast Hire Date to datetime, add Hire Year, Hire Month
        df['Hire Date'] = pd.to_datetime(df['Hire Date'], errors='coerce')
        df = df.dropna(subset=['Hire Date'])
        df['Hire Year'] = df['Hire Date'].dt.year
        df['Hire Year'] = df['Hire Year'].astype('Int16')
        df['Hire Month'] = df['Hire Date'].dt.month
        df['Hire Month'] = df['Hire Month'].astype('Int16')

        # Calculate the number of years employed as a NYC teacher
        df['Years of Employment'] = df['Fiscal Year'] - df['Hire Year']
        df['Years of Employment'] = df['Years of Employment'].astype('Int16')
        df['Years of Employment'] = pd.to_numeric(df['Years of Employment'], errors='coerce')
        df = df.dropna(subset=['Years of Employment'])

        # Create Employee Key
        df[['Last Name', 'First Name', 'Mid Init']] = df[['Last Name', 'First Name', 'Mid Init']].apply(
            lambda x: x.str.strip().str.title().fillna('None')
        )
        df['FirstMidLastStart'] = df['First Name'] + df['Mid Init'] + df['Last Name'] + df['Hire Date'].astype(str)
        df['Employee ID'], _ = pd.factorize(df['FirstMidLastStart'], sort=True)
        df['Employee ID'] = df['Employee ID'].astype('O')
        df = df.drop(columns=['FirstMidLastStart', 'Last Name', 'First Name', 'Mid Init'])

        df = df.sort_values(by=['Employee ID', 'Fiscal Year']).reset_index(drop=True)

        # Cast Salary to an Integer and calculate annual union dues
        union_dues_before_2023 = 63.81*24
        union_dues_2023 = 65.60*24
        df['Salary'] = df['Salary'].astype('int')
        df['UFT Dues'] = np.where(df['Fiscal Year']<=2022,union_dues_before_2023,union_dues_2023)

        # Salary changes YoY
        df['Salary Delta'] = df.groupby(by=['Employee ID'])['Salary'].pct_change() * 100
        df['Salary Monetary Diff'] = df.groupby(by=['Employee ID'])['Salary'].diff()
        
        df[['Salary Delta','Salary Monetary Diff']] = (df[['Salary Delta','Salary Monetary Diff']]
                                                       .fillna(0)
                                                       .round(2)
                                                       )

        ## Categorical Features
        employment_bins = [-1, 5, 10, 15, 20, 25, 60]
        employment_labels = ['0-5', '6-10', '11-15', '16-20', '21-25', '26+']

        # Define bin edges for 'Salary'
        salary_bins = [40000, 60000, 80000, 100000, 120000, 160000]
        salary_labels = ['40k-60k', '60k-80k', '80k-100k', '100k-120k', '120k+']

        # Define bin edges for 'Additional Pay'
        additional_pay_bins = [-10000000,-0.00001,0.00001,500,1000,3000,10000,1000000]
        additional_pay_labels = ['<$0', '$0', '0-$500', '$500-$1K', '$1k-$3K', '$3K-$10K', '$10K+']

        # Define bin edges for 'Salary Delta'
        delta_bins = [-100, 0, 5, 10, 15, 200]
        delta_labels = ['<=0%', '0.01-5%', '5-10%', '10-15%', '15+%']

        # Define bin edges for 'Simplified Salary Delta'
        simplified_delta_bins = [-200, -0.00001, 0.00001, 200]
        simplified_delta_labels = ['Salary Decreased', 'No Change', 'Salary Increased']

        # Define bin edges for 'Salary Monetary Diff'
        monetary_diff_bins = [-60000, 0.0001, 5000, 10000, 15000, 20000, 70000]
        monetary_diff_labels = ['<=0k','1-5k', '5k-10k', '10k-15k', '15k-20k', '20k+']

        # Apply binning to create categorical features
        df['Employment Category'] = pd.cut(df['Years of Employment'], bins=employment_bins, labels=employment_labels)
        df['Salary Category'] = pd.cut(df['Salary'], bins=salary_bins, labels=salary_labels)
        df['Additional Pay Category'] = pd.cut(df['Additional Pay'],bins=additional_pay_bins, labels=additional_pay_labels)
        df['Salary Delta Category'] = pd.cut(df['Salary Delta'], bins=delta_bins, labels=delta_labels)
        df['Salary Simplified Delta Category'] = pd.cut(df['Salary Delta'], bins=simplified_delta_bins, labels=simplified_delta_labels)
        df['Salary Monetary Diff Category'] = pd.cut(df['Salary Monetary Diff'], bins=monetary_diff_bins, labels=monetary_diff_labels)

        # Transform bins into categorical features
        df['Employment Category'] = pd.Categorical(df['Employment Category'],categories=employment_labels,ordered=True)
        df['Salary Category'] = pd.Categorical(df['Salary Category'],categories=salary_labels,ordered=True)
        df['Additional Pay Category'] = pd.Categorical(df['Additional Pay Category'],categories=additional_pay_labels,ordered=True)
        df['Salary Delta Category'] = pd.Categorical(df['Salary Delta Category'],categories=delta_labels,ordered=True)
        df['Salary Simplified Delta Category'] = pd.Categorical(df['Salary Simplified Delta Category'],categories=simplified_delta_labels,ordered=True)
        df['Salary Monetary Diff Category'] =  pd.Categorical(df['Salary Monetary Diff Category'],categories=monetary_diff_labels,ordered=True)

        # Remove outliers
        df = df[(df['Hire Year']>=1980)&
                (df['Years of Employment']<=60)]\
                .sort_values(by=['Employee ID', 'Fiscal Year'])\
                .reset_index(drop=True)
        
        # Add pay schedule features
        df_schedule = pd.read_csv('./data/salary_schedules.csv', engine='pyarrow')
        df_schedule_long = df_schedule.melt(id_vars=['Paystep', 'Salary Schedule'],
                                            var_name='Differential',
                                            value_name='Salary')
        merged_df = pd.merge(df, df_schedule_long, how='left', left_on='Salary', right_on='Salary')

        def get_paystep(row):
            paysteps = merged_df.loc[merged_df['Salary'] == row['Salary'], 'Paystep'].tolist()
            return paysteps[0] if paysteps else 'Other'
        
        def get_differential(row):
            differentials = merged_df.loc[merged_df['Salary'] == row['Salary'], 'Differential'].tolist()
            return differentials[0] if differentials else 'Other'
        
        def get_salary_schedule(row):
            salary_schedule = merged_df.loc[merged_df['Salary'] == row['Salary'], 'Salary Schedule'].tolist()
            return salary_schedule[0] if salary_schedule else 'Other'
        
        df['Paystep'] = df.apply(get_paystep, axis=1)
        df['Differential'] = df.apply(get_differential, axis=1)
        df['Salary Schedule'] = df.apply(get_salary_schedule, axis=1)

        # Add differential requirements and replace missing values
        differential_mapping = {'BA':'Bachelor\'s Degree',
                                'Pre1970':'Pre1970 Teacher',
                                'BA+30':'Bachelor\'s Degree + 30 Credit Hours',
                                'BA+60':'Bachelor\'s Degree + 60 Credit Hours',
                                'BA+66':'Bachelor\'s Degree + 66 Credit Hours',
                                'BA+96':'Bachelor\'s Degree + 96 Credit Hours',
                                'MA':'Master\'s Degree',
                                'MA+':'Master\'s Degree Plus'}
        
        df['Differential Category'] = df['Differential'].map(differential_mapping)

        df[['Paystep', 'Differential', 'Differential Category', 'Salary Schedule']] = df[['Paystep', 'Differential', 'Differential Category', 'Salary Schedule']].fillna('Other')
        
        # Add teacher's degree
        df['Degree'] = np.where(df['Differential Category'].str.contains('Master'), 'Master\'s', df['Differential Category'])
        df['Degree'] = np.where(df['Degree'].str.contains('Bachelor'), 'Bachelor\'s', df['Degree'])
        df['Degree'] = np.where(df['Degree'].str.contains('Pre1970'), 'Other', df['Degree'])

        # Pay schedule categories
        paystep_labels = ['Other','1A', '2A', '3A', '4A', '5A', '6A', '6A+L5', '6B', '6B+L5', '7A',
                          '7A+L5', '7B', '7B+L5', '8A', '8A+L5', '8B', '8B+L5', '8B+L10', '8B+L13',
                          '8B+L15', '8B+L18', '8B+L20', '8B+L22']
        differential_labels = ['Other','BA','Pre1970','BA+30','BA+60','BA+66','BA+96','MA','MA+']
        differential_category_labels = ['Other', 'Bachelor\'s Degree', 'Pre1970 Teacher',
                                        'Bachelor\'s Degree + 30 Credit Hours',
                                        'Bachelor\'s Degree + 60 Credit Hours',
                                        'Bachelor\'s Degree + 66 Credit Hours',
                                        'Bachelor\'s Degree + 96 Credit Hours',
                                        'Master\'s Degree', 'Master\'s Degree Plus']
        salary_schedule_labels = ['Other','2013', '2014 May', '2014 Sept', '2015',
                                  '2016', '2017', '2018 May', '2018 June', '2019',
                                  '2020', '2021', '2022', '2024']
        degree_labels = ['Other', 'Bachelor\'s', 'Master\'s']

        df['Paystep'] = pd.Categorical(df['Paystep'], categories=paystep_labels , ordered=True)
        df['Differential'] = pd.Categorical(df['Differential'], categories=differential_labels , ordered=True)
        df['Differential Category'] = pd.Categorical(df['Differential Category'], categories= differential_category_labels, ordered=True)
        df['Salary Schedule'] = pd.Categorical(df['Salary Schedule'], categories=salary_schedule_labels , ordered=True)
        df['Degree'] = pd.Categorical(df['Degree'], categories=degree_labels, ordered=True)

        # Reorder columns
        df = df[['Fiscal Year',
            'Employee ID',
            'Hire Date',
            'Hire Month',
            'Hire Year',
            'Years of Employment',
            'Employment Category',
            'Salary',
            'Additional Pay',
            'Degree',
            'Paystep',
            'Differential',
            'Differential Category',
            'Salary Schedule',
            'UFT Dues',
            'Salary Category',
            'Additional Pay Category',
            'Salary Delta',
            'Salary Monetary Diff',
            'Salary Simplified Delta Category',
            'Salary Delta Category',
            'Salary Monetary Diff Category'
            ]]

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