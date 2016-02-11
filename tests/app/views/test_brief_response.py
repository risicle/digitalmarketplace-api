import json

from hypothesis import given

from ..helpers import BaseApplicationTest, JSONUpdateTestMixin
from ... import example_listings

from dmapiclient.audit import AuditTypes
from app.models import db, Lot, Brief, BriefResponse, AuditEvent


class BaseBriefResponseTest(BaseApplicationTest):
    def setup(self):
        super(BaseBriefResponseTest, self).setup()

        with self.app.app_context():
            self.setup_dummy_suppliers(1)
            brief = Brief(
                data=example_listings.brief_data().example(),
                status='live', framework_id=5, lot=Lot.query.get(5)
            )
            db.session.add(brief)
            db.session.commit()

            self.brief_id = brief.id

    def create_brief_response(self, data):
        return self.client.post(
            '/brief-responses',
            data=json.dumps({
                'updated_by': 'test@example.com',
                'briefResponses': data,
            }),
            content_type='application/json'
        )

    def get_brief_response(self, brief_response_id):
        return self.client.get('/brief-responses/{}'.format(brief_response_id))


class TestCreateBriefResponse(BaseBriefResponseTest, JSONUpdateTestMixin):
    endpoint = '/brief-responses'
    method = 'post'

    @given(example_listings.brief_response_data())
    def test_create_new_brief_response(self, live_framework, brief_response_data):
        res = self.create_brief_response(dict(brief_response_data, **{
            'briefId': self.brief_id,
            'supplierId': 0,
        }))

        data = json.loads(res.get_data(as_text=True))

        assert res.status_code == 201, data
        assert data['briefResponses']['supplierName'] == 'Supplier 0'
        assert data['briefResponses']['briefId'] == self.brief_id

    @given(example_listings.brief_response_data())
    def test_create_brief_response_creates_an_audit_event(self, live_framework, brief_response_data):
        res = self.create_brief_response(dict(brief_response_data, **{
            'briefId': self.brief_id,
            'supplierId': 0,
        }))

        assert res.status_code == 201, res.get_data(as_text=True)

        with self.app.app_context():
            audit_events = AuditEvent.query.filter(
                AuditEvent.type == AuditTypes.create_brief_response.value
            ).all()

        assert len(audit_events) == 1
        assert audit_events[0].data == {
            'briefResponseId': json.loads(res.get_data(as_text=True))['briefResponses']['id'],
            'briefResponseJson': dict(brief_response_data, **{
                'briefId': self.brief_id,
                'supplierId': 0,
            })
        }

    def test_cannot_create_brief_response_with_empty_json(self, live_framework):
        res = self.client.post(
            '/brief-responses',
            data=json.dumps({
                'updated_by': 'test@example.com',
            }),
            content_type='application/json'
        )

        assert res.status_code == 400

    def test_cannot_create_brief_response_with_invalid_json(self, live_framework):
        res = self.client.post(
            '/brief-responses',
            data=json.dumps({
                'updated_by': 'test@example.com',
                'briefResponses': {
                    'briefId': self.brief_id,
                    'supplierId': 0,
                    'niceToHaveRequirements': 10
                }
            }),
            content_type='application/json'
        )

        data = json.loads(res.get_data(as_text=True))

        assert res.status_code == 400
        assert data['error']['essentialRequirements'] == 'answer_required'
        assert 'niceToHaveRequirements' in data['error']

    def test_cannot_create_brief_response_without_supplier_id(self, live_framework):
        res = self.create_brief_response({
            'briefId': self.brief_id
        })

        assert res.status_code == 400
        assert 'supplierId' in res.get_data(as_text=True)

    def test_cannot_create_brief_response_without_brief_id(self, live_framework):
        res = self.create_brief_response({
            'supplierId': 0
        })

        assert res.status_code == 400
        assert 'briefId' in res.get_data(as_text=True)

    def test_cannot_create_brief_response_with_non_integer_supplier_id(self, live_framework):
        res = self.create_brief_response({
            'briefId': self.brief_id,
            'supplierId': 'not a number',
        })

        assert res.status_code == 400
        assert 'Invalid supplier ID' in res.get_data(as_text=True)

    def test_cannot_create_brief_response_with_non_integer_brief_id(self, live_framework):
        res = self.create_brief_response({
            'briefId': 'not a number',
            'supplierId': 0,
        })

        assert res.status_code == 400
        assert 'Invalid brief ID' in res.get_data(as_text=True)

    def test_cannot_create_brief_response_when_brief_doesnt_exist(self, live_framework):
        res = self.create_brief_response({
            'briefId': self.brief_id + 1,
            'supplierId': 0
        })

        assert res.status_code == 400
        assert 'Invalid brief ID' in res.get_data(as_text=True)

    def test_cannot_create_brief_response_when_supplier_doesnt_exist(self, live_framework):
        res = self.create_brief_response({
            'briefId': self.brief_id,
            'supplierId': 999
        })

        assert res.status_code == 400
        assert 'Invalid supplier ID' in res.get_data(as_text=True)

    def test_cannot_respond_to_a_brief_that_isnt_live(self, live_framework):
        with self.app.app_context():
            brief = Brief(
                data={}, status='draft', framework_id=5, lot=Lot.query.get(5)
            )
            db.session.add(brief)
            db.session.commit()

            brief_id = brief.id

        res = self.create_brief_response({
            'briefId': brief_id,
            'supplierId': 0
        })

        assert res.status_code == 400
        assert "Brief must be live" in res.get_data(as_text=True)

    def test_cannot_respond_to_an_expired_framework_brief(self, expired_framework):
        res = self.create_brief_response({
            'briefId': self.brief_id,
            'supplierId': 0
        })

        assert res.status_code == 400
        assert "Brief framework must be live" in res.get_data(as_text=True)

    @given(example_listings.brief_response_data())
    def test_cannot_respond_to_a_brief_more_than_once_from_the_same_supplier(self, live_framework, brief_response_data):
        self.create_brief_response(dict(brief_response_data, **{
            'briefId': self.brief_id,
            'supplierId': 0,
        }))

        res = self.create_brief_response(dict(brief_response_data, **{
            'briefId': self.brief_id,
            'supplierId': 0,
        }))

        assert res.status_code == 400, res.get_data(as_text=True)
        assert 'Brief response already exists' in res.get_data(as_text=True)

    @given(example_listings.brief_response_data(None, 5).filter(lambda x: len(x['essentialRequirements']) != 5))
    def test_cannot_respond_to_a_brief_with_wrong_number_of_essential_reqs(self, live_framework, brief_response_data):
        res = self.create_brief_response(dict(brief_response_data, **{
            'briefId': self.brief_id,
            'supplierId': 0,
        }))

        data = json.loads(res.get_data(as_text=True))

        assert res.status_code == 400, res.get_data(as_text=True)
        assert data['error']['essentialRequirements'] == 'answer_required'

    @given(example_listings.brief_response_data(5, None).filter(lambda x: len(x['niceToHaveRequirements']) != 5))
    def test_cannot_respond_to_a_brief_with_wrong_number_of_nicetohave_reqs(self, live_framework, brief_response_data):
        res = self.create_brief_response(dict(brief_response_data, **{
            'briefId': self.brief_id,
            'supplierId': 0,
        }))

        data = json.loads(res.get_data(as_text=True))

        assert res.status_code == 400, res.get_data(as_text=True)
        assert data['error']['niceToHaveRequirements'] == 'answer_required'


class TestGetBriefResponse(BaseBriefResponseTest):
    def setup(self):
        super(TestGetBriefResponse, self).setup()

        with self.app.app_context():
            brief_response = BriefResponse(
                data=example_listings.brief_response_data().example(),
                supplier_id=0, brief_id=self.brief_id
            )

            db.session.add(brief_response)
            db.session.commit()

            self.brief_response_id = brief_response.id

    def test_get_brief_response(self):
        res = self.get_brief_response(self.brief_response_id)

        data = json.loads(res.get_data(as_text=True))

        assert res.status_code == 200
        assert data['briefResponses']['id'] == self.brief_response_id
        assert data['briefResponses']['supplierId'] == 0

    def test_get_missing_brief_returns_404(self):
        res = self.get_brief_response(999)

        assert res.status_code == 404
