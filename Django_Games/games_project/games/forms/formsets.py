from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from django.forms.models import BaseModelFormSet
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from games.models import Player, Game, GameScore, Achievement, PlayerAchievement

class BaseGameScoreFormSet(BaseModelFormSet):
    """Custom formset for game scores with validation"""
    
    def clean(self):
        """Validate the formset"""
        if any(self.errors):
            return
        
        total_score = 0
        game_counts = {}
        
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                score = form.cleaned_data.get('score', 0)
                game = form.cleaned_data.get('game')
                
                total_score += score
                
                if game:
                    game_counts[game.id] = game_counts.get(game.id, 0) + 1
                    
                    # Limit scores per game
                    if game_counts[game.id] > 5:
                        raise ValidationError(
                            f"Cannot submit more than 5 scores for {game.display_name}"
                        )
        
        # Check for unrealistic total scores
        if total_score > 10000:
            raise ValidationError("Total score seems unrealistic.")

class GameScoreForm(forms.ModelForm):
    """Individual score form for use in formsets"""
    
    class Meta:
        model = GameScore
        fields = ['game', 'score', 'attempts', 'duration']
        widgets = {
            'game': forms.Select(attrs={'class': 'form-select'}),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '1000'
            }),
            'attempts': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'duration': forms.TimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'MM:SS'
            })
        }
    
    def clean_score(self):
        score = self.cleaned_data.get('score')
        game = self.cleaned_data.get('game')
        
        if game and score > game.max_score:
            raise ValidationError(f"Score cannot exceed {game.max_score} for this game.")
        
        return score

# Create the formset
GameScoreFormSet = modelformset_factory(
    GameScore,
    form=GameScoreForm,
    formset=BaseGameScoreFormSet,
    extra=3,
    max_num=10,
    validate_max=True,
    can_delete=True
)

class MultipleChoiceTestForm(forms.Form):
    """Dynamic form for game quizzes and tests"""
    
    def __init__(self, questions=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if questions:
            for i, question in enumerate(questions):
                field_name = f'question_{i}'
                
                if question['type'] == 'multiple_choice':
                    choices = [(choice['id'], choice['text']) for choice in question['choices']]
                    self.fields[field_name] = forms.ChoiceField(
                        label=question['text'],
                        choices=choices,
                        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
                    )
                elif question['type'] == 'text':
                    self.fields[field_name] = forms.CharField(
                        label=question['text'],
                        max_length=200,
                        validators=[validate_no_profanity],
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )
                elif question['type'] == 'boolean':
                    self.fields[field_name] = forms.BooleanField(
                        label=question['text'],
                        required=False,
                        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                    )
        
        # Add helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit Answers', css_class='btn btn-success'))

# Achievement Assignment Formset
PlayerAchievementFormSet = inlineformset_factory(
    Player,
    PlayerAchievement,
    fields=['achievement', 'progress', 'is_completed'],
    extra=1,
    max_num=20,
    widgets={
        'achievement': forms.Select(attrs={'class': 'form-select'}),
        'progress': forms.NumberInput(attrs={'class': 'form-control'}),
        'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'})
    }
)