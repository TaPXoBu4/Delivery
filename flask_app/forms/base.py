from flask_wtf import FlaskForm
from wtforms.meta import DefaultMeta


class BaseForm(FlaskForm):
    class Meta:
        locales = ["ru"]

        def get_translations(self, form):
            # flask_wtf подменяет переводы на flask-babel (которого нет),
            # поэтому используем стандартный механизм WTForms с Meta.locales
            return DefaultMeta.get_translations(self, form)
