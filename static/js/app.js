const DIAGNOSIS_PAGE_SIZE = 10;

function syncSelectableState() {
    document.querySelectorAll('[data-card-toggle], [data-option-tile], .choice-chip').forEach((tile) => {
        const input = tile.querySelector('input');
        if (!input) {
            return;
        }

        tile.classList.toggle('is-selected', input.checked && tile.hasAttribute('data-card-toggle'));
        tile.classList.toggle('is-checked', input.checked && !tile.hasAttribute('data-card-toggle'));
    });
}

function syncGdprRolePanel() {
    const gdprToggle = document.querySelector('[data-gdpr-toggle]');
    const rolePanel = document.querySelector('[data-gdpr-role-panel]');
    if (!gdprToggle || !rolePanel) {
        return;
    }

    const enabled = gdprToggle.checked;
    rolePanel.classList.toggle('is-hidden', !enabled);
    rolePanel.querySelectorAll('input[name="gdpr_role"]').forEach((input) => {
        input.disabled = !enabled;
    });
}

function syncMapState() {
    const scene = document.querySelector('[data-regulation-map]');
    if (!scene) {
        return;
    }

    const gdprChecked = Boolean(document.querySelector('input[name="selected_regulations"][value="GDPR"]:checked'));
    const ccpaChecked = Boolean(document.querySelector('input[name="selected_regulations"][value="CCPA"]:checked'));
    scene.classList.toggle('is-gdpr', gdprChecked);
    scene.classList.toggle('is-ccpa', ccpaChecked);
}

function handleNoneCheckbox(input) {
    if (input.type !== 'checkbox') {
        return;
    }

    const wrapper = input.closest('[data-question-card]');
    if (!wrapper) {
        return;
    }

    const group = wrapper.querySelectorAll(`input[name="${input.name}"]`);
    if (input.dataset.noneOption === 'true' && input.checked) {
        group.forEach((item) => {
            if (item !== input) {
                item.checked = false;
            }
        });
    }

    if (input.dataset.noneOption !== 'true' && input.checked) {
        group.forEach((item) => {
            if (item.dataset.noneOption === 'true') {
                item.checked = false;
            }
        });
    }
}

function markQuestionValidity(card, valid) {
    card.classList.toggle('is-invalid', !valid);

    let error = card.querySelector('.field-error.client-error');
    if (valid) {
        if (error) {
            error.remove();
        }
        return;
    }

    if (!error) {
        error = document.createElement('p');
        error.className = 'field-error client-error';
        error.textContent = '이 문항에 응답해야 다음 단계로 이동할 수 있습니다.';
        card.appendChild(error);
    }
}

function getDiagnosisCards(form) {
    return Array.from(form.querySelectorAll('[data-question-card]'));
}

function getCardCondition(card) {
    if (card._visibleIf !== undefined) {
        return card._visibleIf;
    }

    const raw = card.dataset.visibleIf;
    if (!raw || raw === 'null') {
        card._visibleIf = null;
        return null;
    }

    try {
        card._visibleIf = JSON.parse(raw);
    } catch (_error) {
        card._visibleIf = null;
    }
    return card._visibleIf;
}

function getCardPageSlot(card) {
    return Number.parseInt(card.dataset.pageSlot || '1', 10) || 1;
}

function getCurrentAnswers(form) {
    const answers = {};
    getDiagnosisCards(form).forEach((card) => {
        const answer = getCardAnswer(card);
        if (answer !== null) {
            answers[card.dataset.questionId] = answer;
        }
    });
    return answers;
}

function getCardAnswer(card) {
    const inputs = Array.from(card.querySelectorAll('input'));
    if (!inputs.length) {
        return null;
    }

    const checked = inputs.filter((input) => input.checked);
    if (!checked.length) {
        return null;
    }

    if (checked[0].type === 'radio') {
        return checked[0].value;
    }
    return checked.map((input) => input.value);
}

function evaluateVisibilityCondition(condition, answers) {
    if (!condition) {
        return true;
    }
    if (Array.isArray(condition.all)) {
        return condition.all.every((item) => evaluateVisibilityCondition(item, answers));
    }
    if (Array.isArray(condition.any)) {
        return condition.any.some((item) => evaluateVisibilityCondition(item, answers));
    }

    const answer = answers[condition.id];
    if (condition.op === 'equals') {
        return answer === condition.value;
    }
    if (condition.op === 'includes') {
        return Array.isArray(answer) && answer.includes(condition.value);
    }
    if (condition.op === 'excludes') {
        return !Array.isArray(answer) || !answer.includes(condition.value);
    }
    if (condition.op === 'one_of') {
        if (Array.isArray(answer)) {
            return condition.values.some((value) => answer.includes(value));
        }
        return condition.values.includes(answer);
    }
    return true;
}

function cardHasAnswer(card) {
    return Array.from(card.querySelectorAll('input')).some((input) => input.checked);
}

function updateDiagnosisStats(form, visibleCards, currentPage, totalPages) {
    const answeredCount = visibleCards.filter((card) => cardHasAnswer(card)).length;
    const remainingCount = Math.max(visibleCards.length - answeredCount, 0);
    const progressPercent = visibleCards.length ? Math.round((answeredCount / visibleCards.length) * 100) : 0;
    const visiblePageSlots = Array.from(new Set(visibleCards.map((card) => getCardPageSlot(card)))).sort((a, b) => a - b);
    const hasPreviousVisiblePage = visiblePageSlots.some((page) => page < currentPage);
    const hasNextVisiblePage = visiblePageSlots.some((page) => page > currentPage);
    const remainingPages = visiblePageSlots.filter((page) => page > currentPage).length;

    const setText = (selector, value) => {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = String(value);
        }
    };

    setText('[data-current-page-label]', currentPage);
    setText('[data-total-pages-label]', totalPages);
    setText('[data-current-page-copy]', currentPage);
    setText('[data-total-pages-copy]', totalPages);
    setText('[data-visible-total]', visibleCards.length);
    setText('[data-answered-count]', answeredCount);
    setText('[data-remaining-count]', remainingCount);
    setText('[data-remaining-pages]', remainingPages);
    setText('[data-progress-percent]', progressPercent);

    const progressFill = document.querySelector('[data-progress-fill]');
    if (progressFill) {
        progressFill.style.width = `${progressPercent}%`;
    }

    const prevButton = form.querySelector('[data-navigation-action="prev"]');
    const nextButton = form.querySelector('[data-navigation-action="next"]');
    const completeButton = form.querySelector('[data-navigation-action="complete"]');

    if (prevButton) {
        prevButton.hidden = !hasPreviousVisiblePage;
    }
    if (nextButton) {
        nextButton.hidden = !hasNextVisiblePage;
    }
    if (completeButton) {
        completeButton.hidden = hasNextVisiblePage;
    }
}

function applyDiagnosisVisibility(form) {
    const cards = getDiagnosisCards(form);
    const pageInput = form.querySelector('[data-page-input]');
    const activeAnswers = {};
    const visibleCards = [];
    const currentPageCards = [];

    const currentPage = Number.parseInt(pageInput?.value || '1', 10) || 1;
    const totalPages = cards.length ? Math.max(...cards.map((card) => getCardPageSlot(card))) : 1;

    cards.forEach((card) => {
        const isVisible = evaluateVisibilityCondition(getCardCondition(card), activeAnswers);
        if (!isVisible) {
            return;
        }
        visibleCards.push(card);
        if (getCardPageSlot(card) === currentPage) {
            currentPageCards.push(card);
        }
        const answer = getCardAnswer(card);
        if (answer !== null) {
            activeAnswers[card.dataset.questionId] = answer;
        }
    });
    const currentPageSet = new Set(currentPageCards);

    cards.forEach((card) => {
        const show = currentPageSet.has(card);
        card.hidden = !show;
        if (!show) {
            markQuestionValidity(card, true);
        }
    });

    currentPageCards.forEach((card, index) => {
        const sequence = cards.indexOf(card) + 1;
        const seq = card.querySelector('[data-question-seq]');
        const count = card.querySelector('[data-question-count]');
        if (seq) {
            seq.textContent = String(sequence).padStart(2, '0');
        }
        if (count) {
            count.textContent = `Q${sequence}`;
        }
    });

    updateDiagnosisStats(form, visibleCards, currentPage, totalPages);
    return { currentPageCards, visibleCards, currentPage, totalPages };
}

function validateDiagnosisForm(form) {
    const { currentPageCards } = applyDiagnosisVisibility(form);
    let firstInvalid = null;

    currentPageCards.forEach((card) => {
        const valid = cardHasAnswer(card);
        markQuestionValidity(card, valid);
        if (!valid && !firstInvalid) {
            firstInvalid = card;
        }
    });

    if (firstInvalid) {
        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    return !firstInvalid;
}

document.addEventListener('DOMContentLoaded', () => {
    syncSelectableState();
    syncGdprRolePanel();
    syncMapState();

    document.addEventListener('change', (event) => {
        const target = event.target;
        if (!(target instanceof HTMLInputElement)) {
            return;
        }

        handleNoneCheckbox(target);
        syncSelectableState();
        syncGdprRolePanel();
        syncMapState();

        const form = target.closest('[data-diagnosis-form]');
        if (form) {
            applyDiagnosisVisibility(form);
            const card = target.closest('[data-question-card]');
            if (card && !card.hidden) {
                markQuestionValidity(card, cardHasAnswer(card));
            }
        }
    });

    document.querySelectorAll('[data-diagnosis-form]').forEach((form) => {
        applyDiagnosisVisibility(form);

        form.addEventListener('submit', (event) => {
            const submitter = event.submitter;
            if (!(submitter instanceof HTMLButtonElement)) {
                return;
            }

            applyDiagnosisVisibility(form);
            const action = submitter.dataset.navigationAction;
            if (action === 'prev') {
                return;
            }

            if (!validateDiagnosisForm(form)) {
                event.preventDefault();
            }
        });
    });
});
