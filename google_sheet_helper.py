import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('g-api-credentials.json', scope)


class GoogleSheetHelper:

    def append_data_on_main_sheet(self, all_test_info):
        gc = gspread.authorize(credentials)
        doc_name = "YOUR_GOOGLE_SHEET_NAME_HERE"
        worksheet = gc.open(doc_name).worksheet("YOUR_WORK_SHEET_NAME_HERE")
        first_cell_value = all_test_info[0]['start_time']
        date_str = str(first_cell_value)
        flag = 0
        try:
            cell = worksheet.find(date_str)
            flag = 1
        except:
            print("No duplicate Found")
        if flag == 1:
            raise Exception("Duplicate entries found!")

        list_of_lists = worksheet.get_all_values()
        real_rows = 0;
        for row in list_of_lists:
            date_stamp = row[0]
            print(date_stamp)
            if date_stamp:
                real_rows = real_rows + 1
            else:
                break
        i = real_rows + 1
        for test_info in all_test_info:
            try:
                device_name = test_info['device_name']
                feature = test_info['feature']
                start_time = test_info['start_time'].strftime("%Y-%m-%d %H:%M:%S")
                scenario = test_info['scenario']
                execution_time = test_info['execution_time']
                error = test_info['error']

                owner = test_info['owner']
                platform = test_info['platform']
                version = test_info['version']
                try:
                    result = test_info['result']
                except:
                    result="FAILED"
                worksheet.update_cell(i, 1, start_time)
                worksheet.update_cell(i, 2, feature)
                worksheet.update_cell(i, 3, scenario)
                worksheet.update_cell(i, 4, execution_time)
                worksheet.update_cell(i, 5, owner)
                worksheet.update_cell(i, 6, platform)
                worksheet.update_cell(i, 7, device_name)
                worksheet.update_cell(i, 8, version)
                worksheet.update_cell(i, 9, "")
                worksheet.update_cell(i, 10, error)
                worksheet.update_cell(i, 11, "")
                worksheet.update_cell(i, 12, result)
                i = i + 1
            except Exception as e:
                print(e)

