/* The panel uses the current app's authenticated session. The server authorizes each action. */
window.DriverReturns = (function () {
  'use strict';
  const label = (ru, en) => TLB.lang() === 'ru' ? ru : en;
  const title = () => label('Возврат заказа', 'Order return');
  let panel;
  let busy = false;

  function add(parent, tag, text) {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    parent.appendChild(node);
    return node;
  }

  function button(parent, text, handler) {
    const node = add(parent, 'button', text);
    node.type = 'button';
    node.addEventListener('click', handler);
    return node;
  }

  function field(form, name, text, type) {
    const row = add(form, 'label', text);
    const input = add(row, 'input');
    input.name = name;
    input.type = type;
    input.required = true;
    if (type === 'number') {
      input.min = name === 'amount' ? '0.01' : '1';
      input.step = name === 'amount' ? '0.01' : '1';
    } else input.maxLength = 200;
    return input;
  }

  function formFor(parent, action, caption, send, options = {}) {
    const form = add(parent, 'form');
    if (options.ref) field(form, 'ref', options.ref, 'text');
    if (options.amount) field(form, 'amount', options.amount, 'number');
    if (options.method) {
      const row = add(form, 'label', label('Способ возврата', 'Refund method'));
      const select = add(row, 'select');
      select.name = 'method';
      add(select, 'option', label('Наличные', 'Cash')).value = 'cash';
      add(select, 'option', label('Перевод', 'Transfer')).value = 'transfer';
    }
    const submit = add(form, 'button', caption);
    submit.type = 'submit';
    submit.dataset.returnAction = action;
    form.addEventListener('submit', event => {
      event.preventDefault();
      const values = new FormData(form);
      send(action, values.get('ref'), values.get('amount'), values.get('method'));
    });
  }

  function money(value) {
    return Number(value).toFixed(2) + ' TJS';
  }

  function build(oid, role, state, note) {
    panel.replaceChildren();
    const heading = add(panel, 'h2', title() + ' #' + oid);
    heading.id = 'driver-return-heading';
    const status = add(panel, 'p', note);
    status.setAttribute('role', 'status');
    status.dataset.returnStatus = '';
    const reload = () => read(oid, role, label('Состояние обновлено.', 'Status refreshed.'));
    const send = async (action, ref, amount, method) => {
      if (busy) return;
      busy = true;
      panel.querySelectorAll('button').forEach(node => { node.disabled = true; });
      status.textContent = label('Сохраняем…', 'Saving…');
      const result = await TLB.writeOrderReturn(oid, action, ref, amount, method);
      // A lost response is reconciled by reading the stored case, never by an automatic write.
      const message = result.error
        ? label('Результат действия не подтверждён. Проверьте сохранённое состояние.',
                'Action result unconfirmed. Check the saved state.')
        : label('Действие сохранено.', 'Action recorded.');
      await read(oid, role, message);
    };
    button(panel, label('Обновить', 'Refresh'), reload);
    button(panel, label('Закрыть', 'Close'), () => panel.close());
    if (!state) return;
    if (!state.departed_at && role === 'driver' && state.can_document_departure) {
      formFor(panel, 'depart', label('Записать оплату и выезд', 'Record payment and departure'), send, {
        ref: label('Номер подтверждения оплаты', 'Payment evidence reference'),
        amount: label('Сумма, фактически уплаченная из своих денег (TJS)', 'Amount actually paid from your own funds (TJS)')
      });
      return;
    }
    if (!state.departed_at) {
      add(panel, 'p', label('Для заказа нет оформленного возврата.', 'This order has no recorded return.'));
      return;
    }
    if (state.cancelled_at) {
      add(panel, 'p', state.received_at
        ? label('Ресторан подтвердил получение блюда.', 'The restaurant acknowledged receiving the meal.')
        : label('Ожидается получение блюда рестораном.', 'Waiting for the restaurant to receive the meal.'));
    } else {
      add(panel, 'p', label('Выезд курьера зафиксирован.', 'Courier departure recorded.'));
      if (role === 'customer' && state.order_status === 'pickedup') {
        add(panel, 'p', label('После отмены курьер вернёт блюдо в ресторан.',
                              'Cancelling sends the meal back to the restaurant.'));
        formFor(panel, 'cancel', label('Подтвердить отмену', 'Confirm cancellation'), send);
      }
      return;
    }
    if (role === 'customer') return;

    add(panel, 'p', label('Оплачено курьером', 'Paid by courier') + ' · ' + money(state.paid));
    add(panel, 'p', label('Подтверждённый возврат', 'Confirmed refund') + ' · ' + money(state.confirmed_refund));
    const claim = add(panel, 'p', label('Остаток требования', 'Outstanding claim') + ' · ' + money(state.open_claim));
    claim.dataset.returnClaim = String(state.open_claim);
    add(panel, 'p', label('К выплате платформой за доставку', 'Outbound delivery due from platform') + ' · ' + money(state.delivery_due));
    if (!state.received_at && role === 'merchant') {
      formFor(panel, 'receive', label('Подтвердить получение блюда', 'Acknowledge meal receipt'), send, {
        ref: label('Номер подтверждения приёма', 'Meal handover evidence reference')
      });
      return;
    }
    if (state.refused_at) add(panel, 'p', label('Отказ в возврате зафиксирован.', 'Refund refusal recorded.'));
    if (state.pending) {
      const pending = state.pending;
      add(panel, 'p', label('Ожидается подтверждение курьера', 'Awaiting courier confirmation') +
        ' · ' + money(pending.amount) + ' · ' + pending.ref + ' · ' +
        (pending.method === 'cash' ? label('Наличные', 'Cash') : label('Перевод', 'Transfer')));
      if (role === 'driver') {
        button(panel, label('Подтверждаю получение денег', 'Confirm money received'),
          () => send('confirm_refund', pending.ref, pending.amount, null)).dataset.returnAction = 'confirm_refund';
        button(panel, label('Оспорить возврат', 'Dispute refund'),
          () => send('dispute_refund', pending.ref, pending.amount, null));
      }
      return;
    }
    if (!state.received_at || state.open_claim <= 0) return;
    if (role === 'merchant') {
      formFor(panel, 'report_refund', label('Записать фактический возврат', 'Record actual refund'), send, {
        ref: label('Номер подтверждения возврата', 'Refund evidence reference'),
        amount: label('Сумма возврата (TJS)', 'Refund amount (TJS)'),
        method: true
      });
    }
    if ((role === 'merchant' || role === 'admin') && !state.refused_at) {
      formFor(panel, 'refuse_refund', label('Зафиксировать отказ', 'Record refusal'), send, {
        ref: label('Подтверждение отказа', 'Refusal evidence reference')
      });
    }
  }

  async function read(oid, role, note) {
    busy = true;
    panel.querySelectorAll('button').forEach(node => { node.disabled = true; });
    const response = await TLB.readOrderReturn(oid);
    busy = false;
    build(oid, role, response.error ? null : response.data, response.error
      ? label('Не удалось прочитать состояние возврата.', 'Could not read the return status.') : note);
  }

  function show() {
    if (!panel) {
      panel = document.createElement('dialog');
      panel.className = 'return-panel';
      panel.setAttribute('aria-labelledby', 'driver-return-heading');
      panel.addEventListener('cancel', event => { if (busy) event.preventDefault(); });
      document.body.appendChild(panel);
    }
    if (!panel.open) panel.showModal();
  }

  async function open(oid, role) {
    if (busy) return;
    show();
    build(oid, role, null, label('Загрузка…', 'Loading…'));
    await read(oid, role);
  }

  function search(role) {
    if (busy) return;
    show();
    panel.replaceChildren();
    add(panel, 'h2', title()).id = 'driver-return-heading';
    const form = add(panel, 'form');
    const input = field(form, 'oid', label('Номер заказа', 'Order number'), 'number');
    add(form, 'button', label('Открыть', 'Open')).type = 'submit';
    button(panel, label('Закрыть', 'Close'), () => panel.close());
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (/^[1-9]\d*$/.test(input.value)) open(input.value, role);
    });
    input.focus();
  }

  return {
    link(order, role) {
      if (!order || !['pickedup', 'cancelled'].includes(order.status) || !/^\d+$/.test(order.id)) return '';
      return '<button type="button" class="b return-link" data-return-order="' + order.id +
        '" onclick="DriverReturns.open(\'' + order.id + '\',\'' + role + '\')">' + title() + '</button>';
    },
    finder(role) {
      return '<button type="button" class="b return-link" onclick="DriverReturns.search(\'' +
        role + '\')">' + label('Найти возврат по заказу', 'Find an order return') + '</button>';
    },
    open, search
  };
})();
