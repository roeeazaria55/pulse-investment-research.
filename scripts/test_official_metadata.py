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
    def test_publisher_card_identity_is_retained_and_not_borrowed(self):
        from official_metadata import organization_key
        p=OfficialPage();p.feed('''<main><article><a href="/search/organization/IREN%2520Limited">IREN</a><h3>IREN reports results</h3><a href="/news-release/iren">Read more</a></article><article><a href="/search/organization/Other%2520Ltd">Other</a><h3>Other discusses IREN</h3><a href="/news-release/other">Read more</a></article></main>''')
        self.assertEqual(p.link_contexts['/news-release/iren']['publisherKey'],organization_key('https://rss.globenewswire.com/en/search/organization/IREN%2520Limited'))
        self.assertEqual(p.link_contexts['/news-release/other']['publisherKey'],'otherltd')
        self.assertEqual(visible_date('07/10/2026'),'2026-10-07')
    def test_generic_report_labels_retain_period_and_filename_provenance(self):
        for label in ('Earning Release','Earnings Release','Investor Presentation'):
            n=describe(C,'https://example.org/uploads/2026/05/ENG_Q3_2025_isa.pdf',label,{'heading':'Q3 2025 financial results'})
            self.assertIn('Q3 2025',n['title']);self.assertEqual(n['documentPeriod'],'Q3 2025')
            self.assertEqual(n['periodBasis'],'index-heading')
            n=describe(C,'https://example.org/uploads/2026/05/ENG_Q3_2025_isa.pdf',label)
            self.assertIn('Q3 2025',n['title']);self.assertEqual(n['periodBasis'],'filename-hint')
            self.assertNotIn('publishedDate',n)
    def test_hebrew_periods_and_underscores_are_only_document_hints(self):
        for filename,period in (('דוח_כספי_רבעון_1_2026_isa.pdf','Q1 2026'),('דוח_תקופתי_2025_isa.pdf','FY 2025'),('דוח-שנתי-2024.pdf','FY 2024')):
            n=describe(C,'https://example.org/uploads/2026/05/'+filename,'View File')
            self.assertEqual(n['documentPeriod'],period);self.assertEqual(n['periodBasis'],'filename-hint')
            self.assertNotIn('publishedDate',n)
        self.assertIsNone(describe(C,'https://example.org/uploads/2026/05/HEB_clean_isa.pdf','HEB')['documentPeriod'])
