#!/usr/bin/python
#-*- coding: utf-8 -*-
# call: script.py %d %s

import gtk
import sys
import os
import re
import shutil
import logging
import logging.config

logging.basicConfig(filename='deploy_wiki.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('deploy_wiki')
#find . -type f \( -iname '*.txt' \) -print0 | xargs -0 grep -c "tegra" | sort -r -k2 -t:

def debug(str):
	logger.debug(str)
	print str


def line_handler(line, attach_dir, deploy_media_dir, image_prefix):
	curly = re.compile('(.*?)\{\{\./(.*?)(\|+.*?)?\}\}(.*)')  #image
	square = re.compile('(.*?)\[\[\./(.*?)(\|+.*?)?\]\](.*)') #link
	debug('line: %s' % line)

	def handler_link(line, myRe, bracket):
		new_line = ''
		m = myRe.match(line)
		while m:
			link_text = os.path.join(image_prefix, m.group(2)).replace(os.sep, ':')
			debug('match: (%d) %s, %s' % (len(m.groups()), m.groups(), link_text))
			new_line += m.group(1) + bracket[0]*2 + link_text
			if os.path.exists(os.path.join(attach_dir, m.group(2))):
				shutil.copy(os.path.join(attach_dir, m.group(2)), os.path.join(deploy_media_dir, m.group(2)))
			if m.group(3):
				new_line += '|' + m.group(3).strip('|')
			new_line += bracket[1]*2
			if m.group(4):
				line = m.group(4)
				m = myRe.match(line)
			else:
				line = ''
				break
		new_line += line
		return new_line

	def handler_empty_line(line):
		if line == '':
			return '\\\\'
		return line

	def handler_bullet_number(line):
		bullet = re.compile('(\t*)\*([^\*].*)')
		number = re.compile('(\t*)-(.*)')
		m = bullet.match(line)
		if m:
			line = '  ' + m.group(1).replace('\t', '  ') + '*' + m.group(2)
		m = number.match(line)
		if m:
			line = '  ' + m.group(1).replace('\t', '  ') + '-' + m.group(2)
		return line

	new_line = handler_link(line, curly, '{}')
	new_line = handler_link(new_line, square, '{}')
	new_line = handler_bullet_number(new_line)
	#new_line = handler_empty_line(new_line)
	debug('	: %s' % new_line)

	return new_line

code_enable = 0
in_paragraph = 0
def paragraph_handler(line, content):
	global code_enable 
	global in_paragraph

	if code_enable == 1:
		if line.startswith('type'):
			splitter = re.compile(r'[= ]')
			l = splitter.split(line)
			print l
			type = l[1]
			filename = "noname"
			if len(l) >= 3:
				filename = l[2]
			
			content += '<file ' + type + ' ' + filename + '>'
			line = ''
		else:
			content += '<file>'
		code_enable = 2
		in_paragraph = 1


	if line == '\'\'\'':
		if code_enable == 0:
			code_enable = 1
		else:
			content += '</file>'
			code_enable = 0
			in_paragraph = 0
		line = ''

	if line.startswith('  '):
		in_paragraph = 1

	# table
	if line.startswith('^') or line.startswith('|'):		 
		debug('start with ^ or |')
		in_paragraph = 1


	if in_paragraph != 0:
		content += line + '\n'
	else:
		content += line + '\n' * 2

	if code_enable == 0 and line.startswith('  '):
		in_paragraph = 0
	# table
	if line.startswith('^') or line.startswith('|'):		 
		in_paragraph = 0

	debug('code_enable: %d, in_paragraph: %d' % (code_enable, in_paragraph))

	return content


def main(notebook_root, wiki_root, user_name, attach_dir, page_path):

	if not os.path.exists(attach_dir):
		os.mkdir(attach_dir)

	attach_relative_dir = os.path.join(user_name, os.path.relpath(attach_dir, notebook_root))
	deploy_page_path = os.path.join(wiki_root, 'data', 'pages', user_name, os.path.relpath(page_path, notebook_root))
	deploy_media_dir = os.path.join(wiki_root, 'data', 'media', attach_relative_dir)

	logger.info('page_path: %s' % page_path)
	logger.info('attach_dir: %s' % attach_dir)
	logger.info('deploy_page_path: %s' % deploy_page_path)
	logger.info('deploy_media_dir: %s' % deploy_media_dir)
	logger.info('attach_relative_dir: %s' % attach_relative_dir)

	new_files_content = ""
	f = open(page_path)

	#skip header
	f.readline()
	f.readline()
	f.readline()

	if not os.path.exists(deploy_media_dir):
		os.makedirs(deploy_media_dir)
	if not os.path.exists(os.path.dirname(deploy_page_path)):
		os.makedirs(os.path.dirname(deploy_page_path))

	for line in f:
		line = line.rstrip()
		line = line_handler(line, attach_dir, deploy_media_dir, attach_relative_dir)
		new_files_content = paragraph_handler(line, new_files_content)
		#new_files_content += r + '\n' * 2

	f.close()

	#print new_files_content
	f = open(deploy_page_path, 'w')
	f.write(new_files_content)
	f.close()
	sys.exit(0)

if __name__ == "__main__":
	if len(sys.argv) == 6:
		logger.info('%s %s %s %s %s %s' % (sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
		main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
	sys.exit(-1)

