import pkg_resources, time, sys, re
import subprocess as sp


def get_pkg_license_txt(pkg, license_txt):

	license_list = ['LICENSE', 'LICENSE.txt', 'LICENCE', 'LICENCE.txt']
	branch_list = ['main', 'master']

	
	if not license_txt:
		for license in license_list:
			try:
				license_txt = pkg.get_metadata(license)

			except:
				pass

			else:
				break

	if not license_txt:

		license_url = ''
		for line in (pkg.get_metadata_lines('METADATA')):
			re_line = re.match(r'(Home-page:|Project-URL:\s+Home(page)?,)\s+https://github\.com/([A-z0-9-_]+?)/([A-z0-9-_]+)', line)

			if re_line:
				break
		
		if not re_line:
			raise Exception(f'ライセンス、またはGitHubへのURLが見つかりません: {pkg}')
		
		for branch in branch_list:

			if license_txt:
				break

			for license in license_list:

				if license_txt:
					break

				license_url = f'https://raw.githubusercontent.com/{re_line[3]}/{re_line[4]}/refs/heads/{branch}/{license}'
				url_result = sp.run(['curl', '-X', 'GET', license_url], capture_output=True, text=True, encoding='utf-8')
				time.sleep(0.5)

				if (url_result.returncode == 0) and (url_result.stdout != '404: Not Found') and (url_result.stdout != ''):
					license_txt = (url_result.stdout)

		
		if not license_txt:
			raise Exception(f'ライセンス、またはGitHubへのURLが見つかりません: {pkg}')

	return license_txt


def create_licenses_txt(ignore_list: list = [], license_dict: dict = {}):

	#-----python本体-----
	with open( (sys.base_prefix+'\\LICENSE.txt') , mode='r', encoding='utf-8') as f:
		python_version = sys.version.split()[0]

		s = (
			'----------------------------------------------------------------------------------------\n'+\
			f'Python {python_version}\n'+\
			'----------------------------------------------------------------------------------------\n'+\
			f'{f.read()}\n'
		)

	#-----ライブラリ-----

	for pkg in sorted(pkg_resources.working_set):
		pkg_name = str(pkg).split()[0]

		if not (pkg_name in ignore_list):
			s += (
				'----------------------------------------------------------------------------------------\n'+\
				f'{str(pkg)}\n'+\
				'----------------------------------------------------------------------------------------\n'+\
				f'{get_pkg_license_txt(pkg, license_dict.get(pkg_name))}\n'
			)
		
	with open('licenses_py.txt', mode='w', encoding='utf-8') as f:
		f.write(s.replace('\r', ''))
	

#ライセンス用テキスト作成君(仮)
if __name__ == "__main__":
	
	#無視するやつをここに記載
	ignore_list = [
		'pyinstaller',
		'pyinstaller-hooks-contrib',
	]

	#取得出来ないやつはここに記載
	license_dict = {
		'pywin32': '''PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2

1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and the Individual or Organization ("Licensee") accessing and otherwise using this software ("Python") in source or binary form and its associated documentation.
2. Subject to the terms and conditions of this License Agreement, PSF hereby grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce, analyze, test, perform and/or display publicly, prepare derivative works, distribute, and otherwise use Python alone or in any derivative version, provided, however, that PSF's License Agreement and PSF's notice of copyright , i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006 Python Software Foundation All Rights Reserved" are retained in Python alone or in any derivative version prepared by Licensee.
3. In the event Licensee prepares a derivative work that is based on or incorporates Python or any part thereof, and wants to make the derivative work available to others as provided herein, then Licensee hereby agrees to include in any such work a brief summary of the changes made to Python.
4. PSF is making Python available to Licensee on an "AS IS" basis. PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED. BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.
5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON, OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
6. This License Agreement will automatically terminate upon a material breach of its terms and conditions.
7. Nothing in this License Agreement shall be deemed to create any relationship of agency, partnership, or joint venture between PSF and Licensee. This License Agreement does not grant permission to use PSF trademarks or trade name in a trademark sense to endorse or promote products or services of Licensee, or any third party.
8. By copying, installing or otherwise using Python, Licensee agrees to be bound by the terms and conditions of this License Agreement.
''',
		'setuptools': '''Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
'''
	}
	
	create_licenses_txt(ignore_list, license_dict)