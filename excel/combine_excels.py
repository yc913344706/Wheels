import xlwings as xw
import os

def get_excel_content(wb):
	shts = wb.sheets
	content_list = []
	for sht in shts:
		des_range = sht.range('A2').current_region
		# print('address -->',des_range.address)
		# content_list.extend(des_range.value[1:])
		content_list.extend(des_range.value)
	return content_list

def get_excels_content(excels_dir, des_app):
	all_excel_contents = []
	file_num = 1
	for excel_tmp in os.listdir(excels_dir):
		print('handling the {} excel --> {}'.format(file_num, excel_tmp))
		file_num += 1
		excel_tmp_path = os.path.join(excels_dir, excel_tmp)
		wb_tmp = des_app.books.open(excel_tmp_path)
		
		excels_content = get_excel_content(wb_tmp)
		all_excel_contents.extend(excels_content)
	
	return all_excel_contents

def output_to_one_excel(all_excel_contents, des_app, des_excel_path):
	wb_tmp = des_app.books.add()
	
	sht_tmp = wb_tmp.sheets[0]
	
	sht_tmp.range('A1').options(expand='table').value = [["资产编号","资产名称","使用人邮箱","备注"]]
	
	sht_tmp.range('A2').options(expand='table').value = all_excel_contents
	
	sht_tmp.autofit()
	
	wb_tmp.save(des_excel_path)

def combine():
	combine_excels_app = xw.App(visible=False,add_book=False)
	
	current_dir = os.path.abspath(os.path.dirname(__file__))
	excels_dir = os.path.join(current_dir, 'excels')
	
	all_excel_contents = get_excels_content(excels_dir, combine_excels_app)
	
	# print(all_excel_contents)
	
	output_to_one_excel(all_excel_contents, combine_excels_app, os.path.join(current_dir, 'result.xlsx'))

	combine_excels_app.kill()
	
def main():
	combine()

if __name__ == "__main__":
	main()