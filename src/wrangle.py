import os
import numpy as np
import pandas as pd


def read_teacher_data(cached_file='./data/teachers_payroll.parquet'):
    '''
    Reads and returns the NYC teachers payroll data from a CSV file.
    
    Parameters:
    - cached_file (str): Path to the cached CSV file containing teachers payroll data.
    
    Returns:
    - pd.DataFrame: DataFrame containing NYC teachers payroll data.
    '''
    df = pd.read_parquet(cached_file)

    df['Fiscal Year'] = df['Fiscal Year'].astype('Int16')
    df['Hire Date'] = pd.to_datetime(df['Hire Date'])
    df['Salary'] = df['Salary'].astype('Int32')
    df['Hire Year'] = df['Hire Year'].astype('Int16')
    df['Years of Employment'] = df['Years of Employment'].astype('Int16')
    df['Employee ID'] = df['Employee ID'].astype('O')
    df['Salary at or Above Schedule Rate'] = df['Salary at or Above Schedule Rate'].astype('Int8')
    df['Compensation at or Above Schedule Rate'] = df['Compensation at or Above Schedule Rate'].astype('Int8')
    df['Salary Monetary Diff Covers UFT Dues'] = df['Salary Monetary Diff Covers UFT Dues'].astype('Int8')
    df['Total Pay Covers UFT Dues'] = df['Total Pay Covers UFT Dues'].astype('Int8')

    employment_labels = ['0-5', '6+']
    contract_labels = ["2009-2018", "2019-2021", "2022-2027"]
    salary_labels = ['40k-60k', '60k-80k', '80k-100k', '100k-120k', '120k+']
    additional_pay_labels = ['$0', '0-$1K', '$1k+']
    delta_labels = ['0%', '0-5%', '5-10%', '10+%']
    simplified_delta_labels = ['No Change', 'Salary Increased']
    monetary_diff_labels = ['0','0-$5k', '$5k-$10k', '$10k+']
    compensation_labels = ['Compensation Decreased', 'No Change', 'Compensation Increased']

    # Transform bins into categorical features
    df['Employment Category'] = pd.Categorical(df['Employment Category'], categories=employment_labels, ordered=True)
    df['Contract Period'] = pd.Categorical(df['Contract Period'],categories=contract_labels,ordered=True)
    df['Salary Category'] = pd.Categorical(df['Salary Category'], categories=salary_labels, ordered=True)
    df['Additional Pay Category'] = pd.Categorical(df['Additional Pay Category'],categories=additional_pay_labels,ordered=True)  
    df['Salary Delta Category'] = pd.Categorical(df['Salary Delta Category'], categories=delta_labels, ordered=True)
    df['Delta Category'] = pd.Categorical(df['Delta Category'],categories=simplified_delta_labels, ordered=True)
    df['Salary Monetary Diff Category'] = pd.Categorical(df['Salary Monetary Diff Category'],
                                                         categories=monetary_diff_labels, ordered=True)
    df['Compensation Category'] = pd.Categorical(df['Compensation Category'],categories=compensation_labels,ordered=True)

    return df


def read_and_filter_data(file_path='city_payroll_data.csv', cached_file='./data/teachers_payroll.parquet'):
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
        cols_to_use = ['Fiscal Year',
                    'Agency Name',
                    'Last Name',
                    'First Name',
                    'Mid Init',
                    'Agency Start Date',
                    'Title Description',
                    'Leave Status as of June 30',
                    'Base Salary',
                    'Total Other Pay']

        data = pd.read_csv('city_payroll_data.csv',
                            usecols=cols_to_use,
                            engine='pyarrow')
        # Filter for teachers that haven't retired
        conditions = (
            (data['Agency Name']=='DEPT OF ED PEDAGOGICAL') &
            (data['Title Description']=='TEACHER') &
            (data['Leave Status as of June 30']!='CEASED')
        )

        cols_to_drop = ['Agency Name',
                        'Title Description',
                        'Leave Status as of June 30']

        # Drop unused columns
        df = data[conditions].drop(columns=cols_to_drop)

        # Rename columns
        df.rename(columns={'Agency Start Date': 'Hire Date',
                        'Base Salary': 'Salary',
                        'Total Other Pay': 'Additional Pay'}, inplace=True)

        # Cast Hire Date to datetime, add Hire Year
        df['Hire Date'] = pd.to_datetime(df['Hire Date'], errors='coerce')

        df['Hire Year'] = df['Hire Date'].dt.year
        df['Hire Year'] = df['Hire Year'].astype('Int16')

        # Calculate the number of years employed
        df['Years of Employment'] = df['Fiscal Year'] - df['Hire Year']
        df['Years of Employment'] = df['Years of Employment'].astype('Int8')

        # Remove outliers
        df = df[df['Years of Employment']<=65]\
                .sort_values('Fiscal Year')\
                .reset_index(drop=True)

        # Create Employee Key
        df[['Last Name', 'First Name', 'Mid Init']] = df[['Last Name', 'First Name', 'Mid Init']].apply(
            lambda x: x.str.replace(' ', '').str.strip().str.title().fillna('None')
        )
        df['FirstMidLastStart'] = df['First Name'] + df['Mid Init'] + df['Last Name'] + df['Hire Date'].astype(str)
        df = df.drop(columns=['Last Name', 'First Name', 'Mid Init'])
        df = df.sort_values(by=['FirstMidLastStart', 'Fiscal Year']).reset_index(drop=True)

        ###################### Feature Engineering #######################################################################
        # Cast Salary to an Integer and calculate annual union dues
        years = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
        dues = [51.87, 53.95, 56.10, 57.19, 58.31, 59.64, 61, 62.39, 63.81, 65.50]
        union_dues = [due*24 for due in dues]
        union_dues_mapping = dict(zip(years, union_dues))
        df['UFT Dues'] = df['Fiscal Year'].map(union_dues_mapping)

        # Calculate the annual salary change YoY as % and $
        df['Additional Pay'] = np.where(df['Additional Pay'] < 0, np.NaN, df['Additional Pay'])
        df['Net Salary'] = df['Salary'] - df['UFT Dues']
        df['Total Pay'] = df['Salary'] + df['Additional Pay']

        # Salary changes YoY
        df['Salary Delta'] = df.groupby(by=['FirstMidLastStart'])['Salary'].pct_change() * 100
        df['Salary Monetary Diff'] = df.groupby(by=['FirstMidLastStart'])['Salary'].diff()
        df['Net Salary Delta'] = df.groupby(by=['FirstMidLastStart'])['Net Salary'].pct_change() * 100
        df['Net Salary Monetary Diff'] = df.groupby(by=['FirstMidLastStart'])['Net Salary'].diff()

        delta_cols = ['Salary Delta',
                      'Salary Monetary Diff',
                      'Net Salary Delta',
                      'Net Salary Monetary Diff']

        df[delta_cols] = df[delta_cols].round(4)

        df['Previous Salary'] = df.groupby('FirstMidLastStart')['Salary'].shift()
        df['Total Pay to Previous Salary Delta'] = (((df['Total Pay']/df['Previous Salary'])-1)*100).round(4)

        # Remove any teachers that had a YoY salary decrease
        df['Salary Delta Flag'] = np.where((df['Salary Delta']>=0)|(df['Salary Delta'].isna()), 1, 0)
        df_salary_filter = df.groupby('FirstMidLastStart')['Salary Delta Flag'].all().reset_index()
        df = df.merge(df_salary_filter, left_on='FirstMidLastStart', right_on='FirstMidLastStart', how='left')
        df = df[df['Salary Delta Flag_y']==True]
        df = df.dropna(subset=['Salary Delta']).reset_index(drop=True).sort_values(by=['FirstMidLastStart', 'Fiscal Year'])

        # Assign a unique ID for the remaining teachers
        df['Employee ID'], _ = pd.factorize(df['FirstMidLastStart'], sort=True)
        df['Employee ID'] = df['Employee ID'].astype('O')
        df = df.drop(columns=['FirstMidLastStart','Salary Delta Flag_x','Salary Delta Flag_y'])
        df = df.sort_values(by=['Employee ID', 'Fiscal Year']).reset_index(drop=True)

        fiscal_year_rates =[1,3,3.5,4.5,5,2,2.5,3,0,3]
        fiscal_rates_mapping = dict(zip(years, fiscal_year_rates))
        df['Fiscal Year Rate'] = df['Fiscal Year'].map(fiscal_rates_mapping.get)

        df['Effective Rate'] = np.where((df['Salary Delta']==0)|(df['Salary Delta'].round(1)<df['Fiscal Year Rate']),
                                         df['Total Pay to Previous Salary Delta'].round(),
                                         df['Salary Delta'].round(1))

        # Define employment bins
        employment_bins = [-1, 5, 70]
        employment_labels = ['0-5', '6+']

        # Define UFT contract bins
        contract_bins = [2009,2018,2021,2027]
        contract_labels = ["2009-2018", "2019-2021", "2022-2027"]

        # Define bin edges for 'Salary'
        salary_bins = [40000, 60000, 80000, 100000, 120000, 160000]
        salary_labels = ['40k-60k', '60k-80k', '80k-100k', '100k-120k', '120k+']

        # Define bin edges for 'Additional Pay'
        additional_pay_bins = [-1, 0, 1000, 94470]
        additional_pay_labels = ['$0', '0-$1K', '$1k+']

        # Define bin edges for 'Salary Delta'
        delta_bins = [-1, 0, 5, 10, 90]
        delta_labels = ['0%', '0-5%', '5-10%', '10+%']

        # Define bin edges for 'Delta Category'
        simplified_delta_bins = [-1, 0, 90]
        simplified_delta_labels = ['No Change', 'Salary Increased']

        # Define bin edges for 'Salary Monetary Diff'
        monetary_diff_bins = [-1, 0, 5000, 10000, 58000]
        monetary_diff_labels = ['0','0-$5k', '$5k-$10k', '$10k+']

        # Define bin edges for 
        effective_rate_bins = [-1,-0.0004,0,90]
        effective_rate_labels = ['Compensation Decreased', 'No Change', 'Compensation Increased']

        # Apply binning to create categorical features
        df['Employment Category'] = pd.cut(df['Years of Employment'], bins=employment_bins, labels=employment_labels)
        df['Contract Period'] = pd.cut(df['Fiscal Year'], bins=contract_bins, labels=contract_labels)
        df['Salary Category'] = pd.cut(df['Salary'], bins=salary_bins, labels=salary_labels)
        df['Additional Pay Category'] = pd.cut(df['Additional Pay'],bins=additional_pay_bins, labels=additional_pay_labels)
        df['Salary Delta Category'] = pd.cut(df['Salary Delta'], bins=delta_bins, labels=delta_labels)
        df['Delta Category'] = pd.cut(df['Salary Delta'], bins=simplified_delta_bins, labels=simplified_delta_labels)
        df['Salary Monetary Diff Category'] = pd.cut(df['Salary Monetary Diff'], bins=monetary_diff_bins, labels=monetary_diff_labels)
        df['Compensation Category'] = pd.cut(df['Effective Rate'], bins=effective_rate_bins, labels=effective_rate_labels)

        # Transform bins into categorical features
        df['Employment Category'] = pd.Categorical(df['Employment Category'],categories=employment_labels,ordered=True)
        df['Contract Period'] = pd.Categorical(df['Contract Period'],categories=contract_labels,ordered=True)
        df['Salary Category'] = pd.Categorical(df['Salary Category'],categories=salary_labels,ordered=True)
        df['Additional Pay Category'] = pd.Categorical(df['Additional Pay Category'],categories=additional_pay_labels,ordered=True)
        df['Salary Delta Category'] = pd.Categorical(df['Salary Delta Category'],categories=delta_labels,ordered=True)
        df['Delta Category'] = pd.Categorical(df['Delta Category'],categories=simplified_delta_labels,ordered=True)
        df['Salary Monetary Diff Category'] =  pd.Categorical(df['Salary Monetary Diff Category'],categories=monetary_diff_labels,ordered=True)
        df['Compensation Category'] = pd.Categorical(df['Compensation Category'],categories=effective_rate_labels,ordered=True)

        df['Salary at or Above Schedule Rate'] = np.where((df['Salary Delta'].round(1) >= df['Fiscal Year Rate']), 1, 0)
        df['Compensation at or Above Schedule Rate'] = np.where(df['Effective Rate']>=df['Fiscal Year Rate'],1,0)
        df['Salary Monetary Diff Covers UFT Dues'] = np.where(df['Salary Monetary Diff']>=df['UFT Dues'], 1, 0)
        df['Total Pay Covers UFT Dues'] = np.where((df['Salary Monetary Diff']+df['Additional Pay'])>=df['UFT Dues'],1,0)

        cols_order = ['Fiscal Year',
        'Employee ID',
        'Hire Date',
        'Hire Year',
        'Years of Employment',
        'Employment Category',
        'Salary',
        'Additional Pay',
        'UFT Dues',
        'Net Salary',
        'Previous Salary',
        'Total Pay',
        'Salary Category',
        'Fiscal Year Rate',
        'Effective Rate',
        'Salary Delta',
        'Net Salary Delta',
        'Total Pay to Previous Salary Delta',
        'Salary Monetary Diff',
        'Net Salary Monetary Diff',
        'Contract Period',
        'Additional Pay Category',
        'Salary Delta Category',
        'Delta Category',
        'Compensation Category',
        'Salary Monetary Diff Category',
        'Salary at or Above Schedule Rate',
        'Compensation at or Above Schedule Rate',
        'Salary Monetary Diff Covers UFT Dues',
        'Total Pay Covers UFT Dues']

        df = df[cols_order]

        # Save teachers payroll dataset
        df.to_parquet('./data/teachers_payroll.parquet', index=False)

        return df


############# Future Analysis ####################
# All education related agencies
# education_agencies = [
# 'DEPT OF ED PER DIEM TEACHERS',
# 'DEPT OF ED PER SESSION TEACHER',
# 'DEPARTMENT OF EDUCATION ADMIN',
# 'DEPT OF ED HRLY SUPPORT STAFF',
# 'DEPT OF ED PARA PROFESSIONALS',
# 'DEPT OF ED PEDAGOGICAL',
# 'TEACHERS RETIREMENT SYSTEM',
# 'NYC EMPLOYEES RETIREMENT SYS'
# ]