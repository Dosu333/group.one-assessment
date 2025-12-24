import logging


class ContextualBrandAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        context = self.extra.get('context', {})

        extra.update({
            'request_id': context.get('request_id', 'system'),
            'brand_id': str(context.get('brand_id', 'unknown')),
            'brand_name': context.get('brand_name', 'unknown'),
        })
        kwargs['extra'] = extra
        return msg, kwargs


def get_logger(name, context):
    return ContextualBrandAdapter(
        logging.getLogger(name), {'context': context})
