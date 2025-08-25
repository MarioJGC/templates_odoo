/* @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { AttachmentList } from "@mail/core/common/attachment_list";
import { patch } from "@web/core/utils/patch";
import { Activity } from "@mail/core/web/activity";

patch(Activity.prototype,{
    setup() {
        super.setup(...arguments);
        this.constructor.components = {
            ...this.constructor.components,
            AttachmentList,
        };
        this.attachmentUploadService = useService("mail.attachment_upload");
    },

    get attachments() {

        let list_attachment = this.props.data.attachment_ids;
    
        if (list_attachment) {
            // Transformar cada attachment sin mutar la lista original
            let updated_attachments = list_attachment.map(attachment => {
                let extension = attachment.name.split('.').pop();
    
                return {
                    ...attachment,
                    extension: extension.toString(),
                    mimetype: `application/${extension.toString()}`,
                    type: "binary",
                    filename: attachment.name,
                    res_name: this.props.data.res_name,
                    url: false,
                    voice: false,
                    uploading: undefined,
                    tmpUrl: undefined,
                    localId: "Attachment," + attachment.id.toString(),
                    accessToken: undefined,
                    create_date: this.props.data.create_date
                };
            });
    
            return updated_attachments;
        }
    
        return [];
    }
    
})