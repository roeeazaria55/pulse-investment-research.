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
    # SEC submissions are untrusted network JSON. A string in `tickers`
    # could otherwise pass substring membership, and zip() would silently
    # truncate unequal filing columns while reporting successful discovery.
    if not isinstance(data,dict) or not isinstance(data.get('tickers'),list) or \
            str(data.get('cik', '')).lstrip('0') != cik or company['ticker'] not in data['tickers']:
        raise ValueError('SEC issuer identity mismatch')
    filings=data.get('filings')
    recent=filings.get('recent') if isinstance(filings,dict) else None
    fields=('form','filingDate','accessionNumber','primaryDocument')
    if not isinstance(recent,dict) or any(not isinstance(recent.get(k),list) for k in fields):
        raise ValueError('Malformed SEC recent filings columns')
    lengths={len(recent[k]) for k in fields}
    if len(lengths)!=1 or next(iter(lengths))>5000:
        raise ValueError('Inconsistent or oversized SEC recent filings columns')
    page=OfficialPage();seen=set()
    for form,date,accession,document in zip(*(recent[k] for k in fields)):
        if not isinstance(form,str) or form not in ('10-K','10-Q','8-K','20-F','6-K'):
            continue
        # Filing dates in this endpoint are DATE ONLY. An ISO-looking prefix
        # followed by arbitrary text is not valid publication evidence.
        if not isinstance(date,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date) or iso_date(date)!=date:
            continue
        if not isinstance(accession,str) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession):
            continue
        if not isinstance(document,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+\.html?',document):
            continue
        url=f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace("-", "")}/{document}'
        if url in seen:continue
        seen.add(url)
        page.links.append((url,f'{company["name"]} — SEC {form} — filed {date}'))
        page.link_contexts[url]={'navigationOnly':False}
        if len(page.links)>=8:break
    return page
