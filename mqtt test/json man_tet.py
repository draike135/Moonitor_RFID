import json

# Your JSON string
json_string = '''{"end_device_ids":{"device_id":"eui-70b3d57ed00678df","application_ids":{"application_id":"eitt2024"},"dev_eui":"70B3D57ED00678DF","join_eui":"0000000000000000","dev_addr":"260BB6D2"},"correlation_ids":["gs:uplink:01HYZVP1M8WKDEXQFC5Q00HVWG"],"received_at":"2024-05-28T15:04:16.476227608Z","uplink_message":{"session_key_id":"AY+/tnW2GWpDbEE5qg5OSw==","f_port":1,"f_cnt":64697,"frm_payload":"MTIzNDU=","rx_metadata":[{"gateway_ids":{"gateway_id":"eui-dca632fffe00861f","eui":"DCA632FFFE00861F"},"time":"2024-05-28T15:04:16.235688Z","timestamp":556721451,"rssi":-54,"channel_rssi":-54,"snr":9,"uplink_token":"CiIKIAoUZXVpLWRjYTYzMmZmZmUwMDg2MWYSCNymMv/+AIYfEKvKu4kCGgsI8OTXsgYQsICIfSD437z5mb3rAQ==","received_at":"2024-05-28T15:04:16.262275120Z"}],"settings":{"data_rate":{"lora":{"bandwidth":125000,"spreading_factor":7,"coding_rate":"4/5"}},"frequency":"868100000","timestamp":556721451,"time":"2024-05-28T15:04:16.235688Z"},"received_at":"2024-05-28T15:04:16.264738878Z","consumed_airtime":"0.051456s","network_ids":{"net_id":"000013","ns_id":"EC656E0000000181","tenant_id":"ttn","cluster_id":"eu1","cluster_address":"eu1.cloud.thethings.network"}}}'''

# Parse the JSON string
data = json.loads(json_string)

# Extract the frm_payload
frm_payload = data['uplink_message']['frm_payload']

# Extract the time from the rx_metadata list
time = data['uplink_message']['rx_metadata'][0]['time']

# Print the extracted values
print("frm_payload:", frm_payload)
print("time:", time)
