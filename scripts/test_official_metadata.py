import unittest
from official_metadata import OfficialPage,describe,visible_date,iso_date,language
C={'name':'Next Vision'}
class MetadataTests(unittest.TestCase):
    def test_clean_generic_labels_and_language_priority(self):
        n=describe(C,'https://example.org/NextVision-FS-2024-גרסה-לתרגום.pdf','\n ENG \n')
        self.assertEqual(n['language'],'en');self.assertEqual(n['titleBasis'],'filename')
        self.assertIn('NextVision FS 2024',n['title']);self.assertNotIn('\n',n['title'])
        self.assertEqual(describe(C,'https://example.org/report.pdf','View File',{'heading':'Q2 2026 Investor Presentation'})['title'],'Q2 2026 Investor Presentation')
    def test_file_or_folder_dates_do_not_become_publication(self):
        n=describe(C,'https://example.org/uploads/2026/08/Q2_2026.pdf','HEB')
        self.assertEqual(n['documentPeriod'],'Q2 2026');self.assertEqual(n['periodBasis'],'filename-hint')
        self.assertNotIn('publishedDate',n);self.assertEqual(n['language'],'he')
    def test_publication_metadata_not_modified_date_or_other_types(self):
        p=OfficialPage();p.feed('<script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-10-01T11:00:00Z","dateModified":"2026-10-18"}</script>')
        self.assertEqual(p.publication_value,'2026-10-01T11:00:00Z')
        p=OfficialPage();p.feed('<meta property="article:modified_time" content="2026-10-18"><time datetime="2026-11-12">Upcoming call</time>')
        self.assertIsNone(p.publication_value)
    def test_adjacent_cards_keep_dates_and_headings_separate(self):
        p=OfficialPage();p.feed('''<main><article><h3>Company to report results on November 12</h3><a href="/news/one">Read more</a><time datetime="2026-10-14">October 14, 2026</time></article><article><h3>Company reports prior results</h3><a href="/news/two">Read more</a><time datetime="2026-08-13">August 13, 2026</time></article></main>''')
        self.assertEqual(p.link_contexts['/news/one']['publishedDate'],'2026-10-14')
        self.assertEqual(p.link_contexts['/news/two']['publishedDate'],'2026-08-13')
        self.assertNotIn('November',p.link_contexts['/news/two']['heading'])
    def test_dates_in_anchor_headline_not_inferred(self):
        p=OfficialPage();p.feed('<a href="/news/a">Company to report results on November 12, 2026</a>')
        self.assertIsNone(p.link_contexts.get('/news/a',{}).get('publishedDate'))
    def test_visible_dates_are_strict(self):
        self.assertEqual(visible_date('October 1, 2026'),'2026-10-01')
        self.assertEqual(visible_date('1 Oct 2026'),'2026-10-01')
        self.assertIsNone(visible_date('Report on October 1, 2026'))
        self.assertIsNone(iso_date('2026-02-30'))
