import os
import errno
import feedparser
import urlparse
import subprocess
import urllib
import tempfile
import sys

# http://export.arxiv.org/oai2?verb=ListSets
RSS_EXTENSIONS = ['astro-ph', 'cond-mat', 'cs', 'econ', \
                  'eess', 'gr-qc', 'hep-ex', 'hep-lat', \
                  'hep-ph', 'hep-th', 'math', 'math-ph', \
                  'nlin', 'nucl-ex', 'nucl-th', 'physics', \
                  'q-bio', 'q-fin', 'quant-ph', 'stat']
RSS_EXTENSIONS = ['eess', 'astro-ph', 'q-fin', 'stat']

ARXIV_RSS_URL = "http://export.arxiv.org/rss/"
ARXIV_PDF_URL = "http://arxiv.org/pdf/"
BASE_PATH = 'arxiv_pdf_imgs'
IMG_SIZE_THRESHOLD = 101000 # in bytes

def create_path_if_nexists(path):
   try:
      os.makedirs(path)
   except OSError as exception:
      if exception.errno != errno.EEXIST:
        raise

def url_path_end(url):
  return url.rsplit('/', 1)[-1]

def arxiv_rss_recent_preprints(extensions, arxiv_rss_url):
   arxiv_articles_dict = {}

   for extension in extensions:
      d = feedparser.parse(urlparse.urljoin(arxiv_rss_url, extension))
      entries = []

      for entry in d.entries:
         entries.append(url_path_end(entry.link))
      arxiv_articles_dict[extension] = entries

   return arxiv_articles_dict

def extract_pdf_images(image_prefix, pdf):
   subprocess.call( ["java",
                    "-jar",
                    "pdfbox-app-2.0.8.jar",
                    "ExtractImages",
                    "-prefix",
                    image_prefix,
                    pdf] )

def del_small_imgs(imgs_dir):
  for dirpath, dirname, filenames in os.walk(imgs_dir):
    for file in filenames:
      abs_file_path = os.path.join(dirpath, file)
      if os.stat(abs_file_path).st_size <= IMG_SIZE_THRESHOLD:
        os.remove(abs_file_path)

def get_img_num(img_filename):
  return int(img_filename[img_filename.rfind('-') + 1 : img_filename.rfind('.')])

def sort_img_names(img_filenames):
  return sorted(img_filenames, key=lambda x: int(get_img_num(x)))

def del_extra_imgs(imgs_dir):
  for dirpath, dirname, filenames in os.walk(imgs_dir):
    sorted_img_files = sort_img_names(filenames)
    for img_file in sorted_img_files[3:]:
      os.remove(os.path.join(dirpath, img_file))

def del_empty_dir(imgs_dir):
  if not os.listdir(imgs_dir):
    os.rmdir(imgs_dir)

def process_articles(arxiv_articles_dict, arxiv_pdf_url):
   for k, v in arxiv_articles_dict.iteritems():
      base_path = os.path.join(BASE_PATH, k)
      create_path_if_nexists(base_path)

      for link_extn in v:
         imgs_dir = os.path.join(base_path, "imgs-" + link_extn)
         article_pdf = link_extn + ".pdf"

         create_path_if_nexists(imgs_dir)
         tmp_pdf = tempfile.NamedTemporaryFile(mode='w+b', prefix='', dir=imgs_dir)
         try:
           urllib.urlretrieve(urlparse.urljoin(arxiv_pdf_url, article_pdf),
                            tmp_pdf.name)
           extract_pdf_images(os.path.join(imgs_dir, "img-" + link_extn),
                            tmp_pdf.name)
         except urllib.ContentTooShortError:
           print "failed download " + article_pdf
           continue
         except IOError as e:
           print "IOError [{0}] : {1}".format(e.errno, e.strerror)
           continue
         except:
           print "Unknown error: ", sys.exc_info()
         
         tmp_pdf.close()
         del_small_imgs(imgs_dir)
         del_extra_imgs(imgs_dir)
         del_empty_dir(imgs_dir)
         


def main():
   process_articles( arxiv_rss_recent_preprints(RSS_EXTENSIONS, ARXIV_RSS_URL), 
                     ARXIV_PDF_URL )

if __name__ == '__main__':
   main()   

   


