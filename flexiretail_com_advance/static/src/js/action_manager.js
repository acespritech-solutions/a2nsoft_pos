odoo.define('flexiretail_com_advance.action_manager', function(require) {
	"use strict";

	var ActionManager = require('web.ActionManager');

	var auto_refresh = false;

	ActionManager.include({
		_onExecuteAction : function(ev) {
			var self = this;
			var actionData = ev.data.action_data;
			var env = ev.data.env;
			if (env.model == 'wizard.pos.x.report'
					&& actionData.id == 'main_print_button') {
				var $session_ids = $("div[name='session_ids']").find('.badge');
				var report_type = $("select[name='report_type']").val();
				var session_ids = [];
				$session_ids.map(function(session) {
					var session_id = $(this).attr('data-id');
					if (Number(session_id)) {
						session_ids.push(Number(session_id));
					}
				});
				return self.do_action('flexiretail_com_advance.report_pos_sales_pdf_front', {
					additional_context : {
						active_ids : session_ids,
					}
				}).fail(function() {
					alert("Connection lost");
				});
			} else {
				return self._super(ev);
			}
		},
	});
});