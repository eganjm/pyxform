from utils import node, SEP, CHOICE_PREFIX
from survey_element import SurveyElement

def _overlay(over, under):
    if type(under)==dict:
        result = under.copy()
        result.update(over)
        return result
    return over if over else under

class Question(SurveyElement):
    def get_type_definition(self):
        qtd = self.get_question_type_dictionary()
        question_type_str = self._dict[self.TYPE]
        return qtd.get_definition(question_type_str)

    def get(self, key):
        """
        Overlay this questions binding attributes on type of the
        attributes from this question type.
        """
        question_type_dict = self.get_type_definition()
        under = question_type_dict.get(key, None)
        over = SurveyElement.get(self, key)
        if not under: return over
        return _overlay(over, under)

    def xml_instance(self):
        return node(self.get_name())
        
    def xml_control(self):
        return None


class InputQuestion(Question):
    """
    This control string is the same for: strings, integers, decimals,
    dates, geopoints, barcodes ...
    """
    def xml_control(self):
        return node(u"input", ref=self.get_xpath(), *self.xml_label_and_hint())


class UploadQuestion(Question):
    def _get_media_type(self):
        return self.get_control()[u"mediatype"]
        
    def xml_control(self):
        return node(
            u"upload",
            ref=self.get_xpath(),
            mediatype=self._get_media_type(),
            *self.xml_label_and_hint()
            )


class Option(SurveyElement):
    VALUE = u"value"

    def __init__(self, *args, **kwargs):
        # if there's no value key then we'll use the name
        # the value and name will be used interchangeably
        value = kwargs.get(self.VALUE,
                           kwargs.get(self.NAME,
                                      None))
        if value is None:
            raise Exception("Did not specify value for multiple choice option", kwargs)
        d = {
            self.LABEL : kwargs[self.LABEL],
            self.NAME : value,
            }
        SurveyElement.__init__(self, **d)
        self._dict[self.VALUE] = value

    def get_value(self):
        return self._dict[self.VALUE]
    
    def xml_value(self):
        return node(u"value", self.get_value())

    def xml(self):
        item = node(u"item")
        item.append(self.xml_label())
        item.append(self.xml_value())
        return item


class MultipleChoiceQuestion(Question):
    def __init__(self, *args, **kwargs):
        kwargs_copy = kwargs.copy()
        choices = kwargs_copy.pop(u"choices", []) + \
            kwargs_copy.pop(u"children", [])
        Question.__init__(self, *args, **kwargs_copy)
        for choice in choices:
            self.add_choice(**choice)
        
    def validate(self):
        Question.validate(self)
        for choice in self.iter_children():
            if choice!=self: choice.validate()
        
    def add_choice(self, **kwargs):
        option = Option(**kwargs)
        self.add_child(option)

    def xml_control(self):
        assert self.get_bind()[u"type"] in [u"select", u"select1"]
        result = node(
            self.get_bind()[u"type"],
            {u"ref" : self.get_xpath()}
            )
        for n in self.xml_label_and_hint():
            result.append(n)
        for n in [o.xml() for o in self._children]:
            result.append(n)                
        return result


class SelectOneQuestion(MultipleChoiceQuestion):
    def __init__(self, *args, **kwargs):
        MultipleChoiceQuestion.__init__(self, *args, **kwargs)
        self._dict[self.TYPE] = u"select one"