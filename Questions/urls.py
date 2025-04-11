from django.urls import path
from Questions import views

urlpatterns = [

    # Question Category urls 
    path('question-category', views.QuestionCategoryView.as_view()),

    # Parent Question urls
    path('parent-question', views.ParentQuestionView.as_view()),

    path('parent-question/<int:parent_question_id>', views.ParentQuestionUpdateView.as_view()),

    path('parent-question-answer/<int:parent_question_id>', views.QuestionAnswerListView.as_view()),

    # Parent Answer urls
    path('parent-answer', views.ParentAnswerView.as_view()),

    path('parent-answer/<int:parent_answer_id>', views.ParentAnswerUpdateView.as_view()),

    # Translated Question urls
    path('translate-question', views.TranslatedQuestionView.as_view()),

    path('translate-question/<int:translated_question_id>', views.TranslatedQuestionUpdateView.as_view()),

    path('translate-question-answer/<int:translated_parent_question_id>', views.TranslatedQuestionAnswerListView.as_view()),

    # Translated Answer urls 
    path('translate-answer', views.TranslatedAnswerView.as_view()),

    path('translate-answer/<int:translated_answer_id>', views.TranslatedAnswerUpdateView.as_view()),

    # question answer list urls 
    path('question-list', views.QuestionAnswerView.as_view({'get':'list'})),

    # translated question answer list urls 
    path('translated-question-list', views.TranslatedQuestionAnswerView.as_view()),
    
    path('translated-question-list/<int:parent_question_id>', views.TranslatedListByParentQuestionListView.as_view()),

    # Parent Question Add by CSV API
    path('parent-question/create-csv-download-xlsx', views.ParentQuestionCreateCSVDownloadXLSX.as_view()),

]