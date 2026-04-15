"""
EduTrack AI — AI Predictor Module
Uses scikit-learn for grade prediction and generates study suggestions.
"""

import numpy as np
from collections import defaultdict


def predict_performance(student_id, grades, attendance):
    """
    Predict end-of-semester GPA and per-subject grades.
    Uses a weighted linear model based on:
      - Current average score per subject
      - Attendance percentage per subject
      - Trend (recent scores improving/declining)

    Returns:
        dict: {
            'predicted_gpa': float,
            'predicted_grade': str,
            'confidence': float,
            'subject_predictions': list
        }
    """
    if not grades:
        return {
            'predicted_gpa': 0.0,
            'predicted_grade': 'N/A',
            'confidence': 0.0,
            'subject_predictions': [],
            'note': 'No grade data available for prediction.'
        }

    # Group grades by subject
    subject_scores = defaultdict(list)
    for g in grades:
        if g.get('max_marks') and g['max_marks'] > 0:
            pct = (g['marks_obtained'] / g['max_marks']) * 100
            subject_scores[g['subject']].append(pct)

    # Build attendance lookup
    attend_map = {}
    for a in attendance:
        if a.get('total') and a['total'] > 0:
            attend_map[a['subject']] = (a['present'] / a['total']) * 100

    subject_predictions = []
    weighted_scores = []

    for subject, scores in subject_scores.items():
        avg_score = np.mean(scores)
        attend_pct = attend_map.get(subject, 75.0)  # default 75% if not found

        # Calculate trend (positive = improving)
        trend_bonus = 0
        if len(scores) >= 2:
            recent = np.mean(scores[-2:])
            earlier = np.mean(scores[:max(1, len(scores)-2)])
            trend_bonus = (recent - earlier) * 0.15  # weight trend at 15%

        # Attendance penalty/bonus
        attend_bonus = 0
        if attend_pct >= 90:
            attend_bonus = 3.0
        elif attend_pct >= 75:
            attend_bonus = 0.0
        elif attend_pct >= 60:
            attend_bonus = -3.0
        else:
            attend_bonus = -7.0

        # Predicted score for this subject
        predicted_score = min(100, max(0, avg_score + trend_bonus + attend_bonus))

        # Convert to grade letter and GPA point
        grade_letter, gpa_point = _score_to_grade(predicted_score)

        subject_predictions.append({
            'subject': subject,
            'current_avg': round(avg_score, 1),
            'predicted_score': round(predicted_score, 1),
            'grade': grade_letter,
            'gpa_point': gpa_point,
            'attendance': round(attend_pct, 1),
            'trend': 'improving' if trend_bonus > 0 else 'declining' if trend_bonus < 0 else 'stable'
        })

        weighted_scores.append(gpa_point)

    # Overall predicted GPA
    predicted_gpa = round(np.mean(weighted_scores), 2) if weighted_scores else 0.0
    overall_grade, _ = _score_to_grade((predicted_gpa / 10.0) * 100)

    # Confidence: higher with more data points
    total_data_points = sum(len(s) for s in subject_scores.values())
    confidence = min(95, 50 + (total_data_points * 3))  # cap at 95%

    return {
        'predicted_gpa': predicted_gpa,
        'predicted_grade': overall_grade,
        'confidence': confidence,
        'subject_predictions': subject_predictions
    }


def get_study_suggestions(grades, attendance):
    """
    Generate actionable study suggestions based on performance data.

    Returns:
        list: [{'subject', 'urgency', 'suggestion', 'hours_recommended'}]
    """
    if not grades:
        return [{'subject': 'All Subjects', 'urgency': 'medium',
                 'suggestion': 'No grade data yet. Keep up with coursework regularly.',
                 'hours_recommended': 2}]

    # Group and compute stats per subject
    subject_scores = defaultdict(list)
    for g in grades:
        if g.get('max_marks') and g['max_marks'] > 0:
            pct = (g['marks_obtained'] / g['max_marks']) * 100
            subject_scores[g['subject']].append(pct)

    attend_map = {}
    for a in attendance:
        if a.get('total') and a['total'] > 0:
            attend_map[a['subject']] = (a['present'] / a['total']) * 100

    suggestions = []

    for subject, scores in subject_scores.items():
        avg = np.mean(scores)
        attend_pct = attend_map.get(subject, 75.0)

        if avg < 50:
            urgency = 'critical'
            suggestion = (
                f"Critical: Averaging {avg:.0f}% in {subject}. "
                f"Meet with your professor, review all lecture notes, and attempt past question papers."
            )
            hours = 6
        elif avg < 65:
            urgency = 'high'
            suggestion = (
                f"Weak performance in {subject} ({avg:.0f}%). "
                f"Dedicate focused study sessions and solve practice problems daily."
            )
            hours = 4
        elif avg < 75:
            urgency = 'medium'
            suggestion = (
                f"Average performance in {subject} ({avg:.0f}%). "
                f"Review weaker chapters and attempt more quiz-style questions."
            )
            hours = 3
        elif avg < 85:
            urgency = 'low'
            suggestion = (
                f"Good performance in {subject} ({avg:.0f}%). "
                f"Maintain consistency and explore advanced topics for extra credit."
            )
            hours = 2
        else:
            urgency = 'minimal'
            suggestion = (
                f"Excellent in {subject} ({avg:.0f}%). "
                f"Continue current pace. Consider helping classmates to reinforce your knowledge."
            )
            hours = 1

        # Attendance warning override
        if attend_pct < 75 and urgency in ('low', 'minimal'):
            urgency = 'medium'
            suggestion += f" Also: attendance is at {attend_pct:.0f}% — aim for 90%+."
            hours = max(hours, 2)

        suggestions.append({
            'subject': subject,
            'urgency': urgency,
            'suggestion': suggestion,
            'current_avg': round(avg, 1),
            'attendance': round(attend_pct, 1),
            'hours_recommended': hours
        })

    # Sort: critical first
    urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'minimal': 4}
    suggestions.sort(key=lambda x: urgency_order.get(x['urgency'], 5))

    return suggestions


def _score_to_grade(score):
    """
    Convert a percentage score to a letter grade and GPA point (10-point scale).
    """
    if score >= 90:  return 'A+', 10.0
    if score >= 85:  return 'A',  9.0
    if score >= 80:  return 'B+', 8.0
    if score >= 75:  return 'B',  7.0
    if score >= 70:  return 'C+', 6.0
    if score >= 65:  return 'C',  5.0
    if score >= 60:  return 'D',  4.0
    return 'F', 0.0


def recommend_study_hours(subject_averages):
    """
    Given a dict of {subject: avg_pct}, return recommended weekly study hours per subject.
    """
    recommendations = {}
    for subject, avg in subject_averages.items():
        if avg < 50:   recommendations[subject] = 6
        elif avg < 65: recommendations[subject] = 4
        elif avg < 75: recommendations[subject] = 3
        elif avg < 85: recommendations[subject] = 2
        else:          recommendations[subject] = 1
    return recommendations
