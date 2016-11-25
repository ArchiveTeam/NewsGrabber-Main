import codecs
import os

import warc


class Deduplicate(object):
    records = {}

    def __init__(self, f):
        self.input_filename = f
        self.input_file = warc.WARCFile(self.input_filename)
        self.input_file_size = os.path.getsize(self.input_filename)

        self.output_filename = self.input_filename[:-8] + '-deduplicated.warc.gz'
        open(self.output_filename+'.upload', 'w').close()
        self.output_file = warc.WARCFile(self.output_filename, 'w')

        open(self.output_log_filename+'.upload', 'w').close()
        self.output_log_filename = self.input_filename[:-8] + '-deduplicated.log'
        self.output_log = []

    def deduplicate(self):
        info_record = self.input_file.read_record()
        info_record.header['WARC-Filename'] = self.output_filename
        del info_record.header['WARC-Block-Digest']

        self.output_file.write_record(warc.WARCRecord(
            payload=info_record.payload.read(),
            header=info_record.header,
            defaults=False))

        while self.input_file_size > self.input_file.tell():
            for record in self.input_file:
                if record.type == 'response':
                    record = self.deduplicate_record(record)
                else:
                    record = warc.WARCRecord(
                        header=record.header,
                        payload=record.payload.read(),
                        defaults=False)
                self.output_file.write_record(record)

        self.input_file.close()
        self.output_file.close()

        with codecs.open(self.output_log_filename, 'w') as output_log_file:
            output_log_file.write('\r\n'.join(self.output_log))

        if self.double_check(self.input_filename):
            os.remove(self.input_filename)
            os.remove(self.input_filename+'.upload')
        else:
            os.remove(self.output_filename)
            os.remove(self.output_log_filename)
            os.remove(self.output_filename+'.upload')
            os.remove(self.output_log_filename+'.upload')

    def deduplicate_record(self, record):
        record_check = self.check_record(record)
        if record_check:
            record_headers = []
            record_payload_ = record.payload.read()

            for line in record_payload_.splitlines():
                if line in ['\r\n', '\n', '']:
                    break
                record_headers.append(line.strip())
            record_payload = '\r\n'.join(record_headers) + '\r\n'*2

            if not ('Content-Length: 0' in record_payload \
                  or 'content-length: 0' in record_payload):
                record.header['Content-Length'] = str(len(record_payload))
                record.header['WARC-Refers-To'] = \
                    record_check['WARC-Record-ID']
                record.header['WARC-Refers-To-Date'] = \
                    record_check['WARC-Date']
                record.header['WARC-Refers-To-Target-URI'] = \
                    record_check['WARC-Target-URI']
                record.header['WARC-Type'] = 'revisit'
                record.header['WARC-Truncated'] = 'length'
                record.header['WARC-Profile'] = \
                    'http://netpreserve.org/warc/1.0/revisit/identical-payload-digest'
                del record.header['WARC-Block-Digest']

                self.output_log.append('WARC-Record-ID:{dID}; ' \
                    'WARC-Target-URI:{dURL}; WARC-Date:{dDate} ' \
                    'duplicate of WARC-Record-ID:{oID}; ' \
                    'WARC-Target-URI:{oURL}; WARC-Date:{oDate}' \
                    .format(dID=record.header['WARC-Record-ID'],
                    dURL=record.header['WARC-Target-URI'],
                    dDate=record.header['WARC-Date'],
                    oID=record_check['WARC-Record-ID'],
                    oURL=record_check['WARC-Target-URI'],
                    oDate=record_check['WARC-Date']))

                return warc.WARCRecord(
                    header=record.header,
                    payload=record_payload,
                    defaults=False)
            else:
                return warc.WARCRecord(
                    header=record.header,
                    payload=record_payload_,
                    defaults=False)
        else:
            return warc.WARCRecord(
                header=record.header,
                payload=record.payload.read(),
                defaults=True)

    @classmethod
    def check_record(cls, record):
        record_hash = record.header.get('WARC-Payload-Digest') \
            .split(':', 1)[1]
        record_url = record.header.get('WARC-Target-URI')
        record_id = record.header.get('WARC-Record-ID')
        record_date = record.header.get('WARC-Date')
        element = ','.join([record_url, record_hash])

        if element in cls.records:
            return cls.records[element]

        cls.records[element] = {'WARC-Target-URI': record_url,
            'WARC-Record-ID': record_id,
            'WARC-Date': record_date}

        return False

    @classmethod
    def double_check(cls, f):
        input_file = warc.WARCFile(f)
        input_file_size = os.path.getsize(f)
        input_file_records = 0
        output_filename = f[:-8] + '-deduplicated.warc.gz'
        output_file = warc.WARCFile(output_filename)
        output_file_size = os.path.getsize(output_filename)
        output_file_records = 0

        while input_file_size > input_file.tell():
            for record in input_file:
                input_file_records += 1

        while output_file_size > output_file.tell():
            for record in output_file:
                output_file_records += 1

        print f, input_file_records
        print output_filename, output_file_records

        return input_file_records == output_file_records