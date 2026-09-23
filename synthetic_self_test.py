from pathlib import Path
import importlib.util, sys, types, tempfile
root=Path(__file__).resolve().parent
pkg=types.ModuleType('powertech_gate');pkg.__path__=[str(root/'custom_components/powertech_gate')];sys.modules['powertech_gate']=pkg
const=types.ModuleType('powertech_gate.const');const.BACKEND_BASE_URL='https://invalid.example';const.BACKEND_REST_TOKEN='unused';const.KNOWN_PEDESTRIAN_MODELS={'PS20088','PS20088D','PS20040','PS20040D'};sys.modules['powertech_gate.const']=const
spec=importlib.util.spec_from_file_location('powertech_gate.backend',root/'custom_components/powertech_gate/backend.py');b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)
uuid='00000000-0000-0000-0000-000000000001'; endpoint='test-endpoint.iot.example'
original=b._request
for device_record, expected_endpoint in [({'uuid':uuid,'devies_type':'PS20088'},''),({'uuid':uuid,'devies_type':'PS20088','iot_endpoint':'initial-endpoint.example'},'initial-endpoint.example')]:
 b._request=lambda *args, **kwargs: {'admin_devices':[device_record],'user_devices':[],'share_devices':[],'custom_info':[]}
 found=b.get_devices('fake-token');assert len(found)==1;assert found[0].endpoint==expected_endpoint
 print('PASS: discovery with endpoint' if expected_endpoint else 'PASS: discovery without endpoint')
b._request=original
# Ensure an endpoint-less candidate provisions with certificate endpoint, not its missing original one.
selected=b.PowertechDevice(uuid=uuid,endpoint='',label='test')
original_create_certificate=b.create_user_certificate
b.create_user_certificate=lambda token:(endpoint,'arn:test','cert','key')
observed={}
b.attach_policy=lambda token, *,endpoint,certificate_arn,uuid: observed.update(endpoint=endpoint,uuid=uuid)
b.save_credentials=lambda base_directory, *,uuid,certificate_pem,private_key: ('cert.path','key.path')
returned,cert,key=b.provision(access_token='fake',device=selected,credentials_base_directory=tempfile.gettempdir())
assert returned==endpoint and observed=={'endpoint':endpoint,'uuid':uuid}
print('PASS: endpoint-less provisioning uses certificate endpoint')
# A response missing certificate endpoint must still fail safe.
b._request=lambda *args, **kwargs: {'user_certificateArn':'arn','certificatePem':'cert','PrivateKey':'key'}
try: original_create_certificate('fake')
except b.CertificateProvisionError: print('PASS: missing certificate endpoint fails closed')
else: raise AssertionError('Missing certificate endpoint was accepted')
