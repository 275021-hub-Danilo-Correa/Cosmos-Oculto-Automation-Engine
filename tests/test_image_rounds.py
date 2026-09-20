import io
import os
import unittest
from unittest.mock import patch
from PIL import Image
import test_regressions as regression

from coae.image_rounds import create_round, process_round, cancel_round


class ImageRoundTests(unittest.TestCase):
    def setUp(self):
        regression.ApplicationTests.setUp(self)
        regression.ApplicationTests.prepared(self)
        self.env=patch.dict(os.environ,{'COAE_TEXT_PROVIDER':'ollama','COAE_IMAGE_PROVIDER':'comfyui'})
        self.env.start()
        stream=io.BytesIO();Image.new('RGB',(320,180),'navy').save(stream,format='PNG');self.raw=stream.getvalue()
    def tearDown(self):
        self.env.stop();regression.ApplicationTests.tearDown(self)
    def factory(self):
        factory=patch('coae.image_rounds.ComfyUI').start();self.addCleanup(patch.stopall)
        client=factory.return_value
        client.metadata.return_value={'workflow':'{"fixture":true}','model':'fixture.safetensors'}
        def generate(prompt,ticket,persist,**kwargs):
            persist({'prompt_id':'prompt-'+str(kwargs['seed']),'fingerprint':'fixture','status':'DONE'})
            kwargs['progress']('Gerando no ComfyUI',None,'prompt-'+str(kwargs['seed']))
            return self.raw,{'provider':'comfyui','prompt_id':'prompt-'+str(kwargs['seed'])}
        client.generate.side_effect=generate
        return client
    def fake_audit(self,pid,iid):
        issues=[{'code':code,'message':'Imagem adequada em '+code,'severity':'review'} for code in
                ('SPEECH_MATCH','MISSING_CONTRADICTORY','SCIENCE','VISUAL_QUALITY','SUGGESTIONS')]
        return self.app.store_audit(pid,'image',iid,issues)
    def fake_remote(self,pid,role,task,data,image=None):
        if 'Prepare um prompt curto' in task:
            return {'positive_prompt':'Photorealistic wide deep-space star field, varied natural stellar colors and brightness, dark scientific documentary, coherent composition, low-key light, vast scale and depth.',
                    'negative_prompt':'text, diagram, infographic, planet, landscape, illustration'}
        return {'recommended_candidate':2,'summary':'A segunda corresponde melhor à fala.'}
    def test_two_variations_are_recorded_audited_recommended_and_one_approved(self):
        self.factory()
        rid=create_round(self.app,self.pid,'SC001',2)
        with patch.object(self.app,'image_audit',side_effect=self.fake_audit),patch.object(self.app,'remote',side_effect=self.fake_remote):
            process_round(self.app,rid)
        state=self.app.state(self.pid);candidates=[c for c in state['image_candidates'] if c['round_id']==rid]
        self.assertEqual([c['status'] for c in candidates],['DONE','DONE'])
        self.assertEqual(len({c['seed'] for c in candidates}),2)
        self.assertTrue(all(c['prompt'] and c['workflow'] and c['model'] and c['prompt_id'] and c['audit_id'] for c in candidates))
        round_row=next(r for r in state['image_rounds'] if r['id']==rid)
        self.assertEqual(round_row['recommendation_image_id'],candidates[1]['image_id'])
        self.app.approve_image(self.pid,candidates[0]['image_id'],'Primeira candidata conferida por uma pessoa.')
        self.app.approve_image(self.pid,candidates[1]['image_id'],'Segunda candidata conferida por uma pessoa.')
        approved=[i for i in self.app.state(self.pid)['images'] if i['status']=='APPROVED']
        self.assertEqual([i['id'] for i in approved],[candidates[1]['image_id']])
    def test_rejection_starts_exactly_one_new_round_without_seed_reuse(self):
        self.factory();first=create_round(self.app,self.pid,'SC001',2)
        second=create_round(self.app,self.pid,'SC001',3,'')
        rows=self.app.state(self.pid)['image_rounds'];self.assertEqual(len(rows),2)
        self.assertEqual(next(r for r in rows if r['id']==first)['status'],'REJECTED')
        seeds=[c['seed'] for c in self.app.state(self.pid)['image_candidates']]
        self.assertEqual(len(seeds),len(set(seeds)));self.assertEqual(len([c for c in self.app.state(self.pid)['image_candidates'] if c['round_id']==second]),3)
    def test_cancel_preserves_completed_candidate(self):
        self.factory();rid=create_round(self.app,self.pid,'SC001',2)
        self.db.execute("UPDATE image_candidates SET status='DONE' WHERE round_id=? AND candidate_number=1",(rid,))
        cancel_round(self.app,self.pid,rid);result=process_round(self.app,rid)
        candidates=self.app.state(self.pid)['image_candidates']
        self.assertEqual(candidates[0]['status'],'DONE');self.assertEqual(candidates[1]['status'],'CANCELLED')
        self.assertIn('cancelada',result['message'])


if __name__=='__main__':unittest.main()
