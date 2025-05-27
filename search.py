import base64
import string

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from sklearn.feature_extraction import _stop_words
from rank_bm25 import BM25Okapi
import logfire
import torch

num_top_hits = 5


if not torch.cuda.is_available():
    logfire.warn("CUDA is not available. Searching on CPU.")

# use https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2
bi_encoder = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")
top_k = 32
# TODO: potentially tweak

cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")


def bm25_tokenizer(text: str) -> list[str]:
    """
    Tokenize a string using the BM25 algorithm.
    """
    tokenized_text = []
    for token in text.lower().split():
        token = token.strip(string.punctuation)
        if len(token) > 0 and token not in _stop_words.ENGLISH_STOP_WORDS:
            tokenized_text.append(token)
    return tokenized_text


def search(data: list[dict], query: str) -> list[dict]:
    """
    Search for a query in the given data.

    param data: A list of dictionaries containing data to search.
        - Each dictionary must contain a key named "data" that contains the data to search.
    """
    logfire.span("Refining search results...")

    data_embedding = bi_encoder.encode(
        [
            data_blob['data'] for data_blob in data # TODO unsure
        ],
        convert_to_tensor=True,
        show_progress_bar=True
    )

    tokenized_data = []
    for data_node in data:
        tokenized_data.append(bm25_tokenizer(data_node['data']))
    bm25 = BM25Okapi(tokenized_data)

    bm25_scores = bm25.get_scores(bm25_tokenizer(query))
    top_n = np.argpartition(bm25_scores, -5)[-5:] #TODO maybe tweak 2
    bm25_hits = [{'data_id': idx, 'score': bm25_scores[idx]} for idx in top_n]
    bm25_hits = sorted(bm25_hits, key=lambda x: x['score'], reverse=True)

    query_embedding = bi_encoder.encode(query, convert_to_tensor=True)
    if torch.cuda.is_available():
        query_embedding = query_embedding.cuda()
    else:
        logfire.warn("CUDA is not available. Might be slow...")
    hits = util.semantic_search(query_embedding, data_embedding, top_k=top_k)
    hits = hits[0]

    ### RERANKING ###
    cross_input = [[query, data[hit['corpus_id']]['data']] for hit in hits]
    cross_scores = cross_encoder.predict(cross_input)
    for idx in range(len(cross_scores)):
        hits[idx]['cross_score'] = cross_scores[idx] # TODO need .tolist() ?

    top_hits_bm25 = bm25_hits[:num_top_hits]
    top_hits_bi_encoder = sorted(hits, key=lambda x: x['score'], reverse=True)[:num_top_hits]
    top_hits_cross = sorted(hits, key=lambda x: x['cross_score'], reverse=True)[:num_top_hits]

    out_data = []

    logfire.span("Results:", _level='debug')
    logfire.span("BM25 top hits:", _level='debug')
    for idx, hit in enumerate(top_hits_bm25):
        logfire.debug(f"{idx+1}. {data[hit['data_id']]} ({hit['score']})")
    logfire.span("Bi-Encoder top hits:", _level='debug')
    for idx, hit in enumerate(top_hits_bi_encoder):
        logfire.debug(f"{idx+1}. {data[hit['corpus_id']]} ({hit['score']})")
    logfire.span("Cross Encoder top hits:", _level='debug')
    for idx, hit in enumerate(top_hits_cross):
        logfire.debug(f"{idx+1}. {data[hit['corpus_id']]} ({hit['cross_score']})")
        out_data.append(data[hit['corpus_id']])

    return out_data


def decode_base64url(data):
    """Decode base64url to string."""
    return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4)).decode('utf-8')


def preprocess_emails(emails: list[dict]) -> list[dict]:
    """
    Preprocess e-mails for search.
    """
    preprocessed_emails = []
    for email in emails:
        subject = [pair['value'] for pair in email['payload']['headers'] if pair['name'] == 'Subject'][0]
        sender = [pair['value'] for pair in email['payload']['headers'] if pair['name'] == 'From'][0]
        if not email['payload']:
            logfire.warn("No payload found in email.")
            continue

        plain_body = None
        html_body = None
        if not email['payload'].get('parts'):
            logfire.warn("No parts found in email.")
            continue
        for part in email['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                plain_body_encoded = part['body']['data']
                plain_body = decode_base64url(plain_body_encoded)
                break
            if part['mimeType'] == 'text/html':
                html_body_encoded = part['body']['data']
                html_body = decode_base64url(html_body_encoded)
                break
        if not plain_body and not html_body:
            logfire.warn("No plain text or HTML body found in email.")
            continue

        preprocessed_emails.append({
            'data':
                f'from: {sender}'
                f'\n\n'
                f'subject: {subject}'
                f'\n\n'
                f'body: {plain_body or html_body or email["snippet"]}',
            'id': email['id']
        })
    return preprocessed_emails