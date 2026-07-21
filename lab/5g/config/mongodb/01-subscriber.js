const open5gs = db.getSiblingDB('open5gs');

open5gs.subscribers.updateOne(
  { imsi: '001011234567891' },
  {
    $set: {
      schema_version: 1,
      msisdn: [],
      imeisv: [],
      mme_host: [],
      mme_realm: [],
      purge_flag: [],
      access_restriction_data: 32,
      subscriber_status: 0,
      operator_determined_barring: 0,
      network_access_mode: 0,
      subscribed_rau_tau_timer: 12,
      security: {
        k: '00000000000000000000000000000000',
        amf: '8000',
        op: null,
        opc: '00000000000000000000000000000000'
      },
      ambr: {
        downlink: { value: 1, unit: 3 },
        uplink: { value: 1, unit: 3 }
      },
      slice: [
        {
          sst: 1,
          sd: '000001',
          default_indicator: true,
          session: [
            {
              name: 'internet',
              type: 3,
              qos: {
                index: 9,
                arp: {
                  priority_level: 8,
                  pre_emption_capability: 1,
                  pre_emption_vulnerability: 1
                }
              },
              ambr: {
                downlink: { value: 1, unit: 3 },
                uplink: { value: 1, unit: 3 }
              },
              pcc_rule: []
            }
          ]
        }
      ]
    }
  },
  { upsert: true }
);

print('Hatch 5G Lab subscriber is ready: 001011234567891');
