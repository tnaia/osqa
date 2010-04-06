from forum.models import Question

def question_search(keywords, orderby):
    return Question.objects.filter(deleted=False).extra(
                    where=["tsv @@ plainto_tsquery(%s)"],
                    params=[keywords],
                    select_params=[keywords]
                ).order_by(orderby, '-ranking')