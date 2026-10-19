"""Bounded SEC submission metadata; archive paths are scoped to the issuer CIK."""
import json
import re
import urllib.request
from official_metadata import OfficialPage, iso_date


def submissions_page(source, company, loader=None):
    cik = str(source['cik'])
    if not re.fullmatch(r'[1-9][0-9]{0,9}', cik):
        raise ValueError('Invalid SEC issuer identifier')
    expected = f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json'
    if source['url'] != expected or f'/Archives/edgar/data/{cik}/' not in company['documentPaths']:
        raise ValueError('SEC source does not match issuer archive')
    if loader is None:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                raise ValueError('SEC metadata redirects rejected')
        request = urllib.request.Request(expected, headers={
            'User-Agent': 'PULSE public research https://github.com/roeeazaria55/pulse-investment-research.',
            'Accept': 'application/json'})
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=12) as response:
            raw = response.read(2*1024*1024+1)
        if len(raw)>2*1024*1024:
            raise ValueError('SEC metadata size limit')
        data=json.loads(raw)
    else:
        data=loader(expected)
    if str(data.get('cik', '')).lstrip('0') != cik or company['ticker'] not in data.get('tickers', []):
        raise ValueError('SEC issuer identity mismatch')
    recent=data['filings']['recent'];page=OfficialPage()
    for form,date,accession,document in zip(recent['form'],recent['filingDate'],recent['accessionNumber'],recent['primaryDocument']):
        if form not in ('10-K','10-Q','8-K','20-F','6-K') or not iso_date(date):
            continue
        if not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession) or not re.fullmatch(r'[A-Za-z0-9_.-]+\.html?',document):
            continue
        url=f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace("-", "")}/{document}'
        page.links.append((url,f'{company["name"]} — SEC {form} — filed {date}'))
        page.link_contexts[url]={'navigationOnly':False}
        if len(page.links)>=8:break
    return page
