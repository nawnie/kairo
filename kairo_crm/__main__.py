"""One request per line over stdin; local development adapter, no HTTP auth."""
import json
import sys
from dataclasses import asdict
from .engine import Context, Evidence, review


def main():
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if request.get('operation') != 'review':
                raise ValueError('only review supported by this transport')
            context = Context(**request['context'])
            evidence = [Evidence(**item) for item in request['evidence']]
            result = asdict(review(context, evidence, request['record_id'],
                                   request['field'], request['now']))
            print(json.dumps({'ok': True, 'result': result}, allow_nan=False), flush=True)
        except (ValueError, TypeError, KeyError):
            print(json.dumps({'ok': False, 'error': 'invalid_request'}), flush=True)


if __name__ == '__main__':
    main()
