import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import {defineMessage, FormattedMessage, useIntl} from 'react-intl';

import FormRow from 'components/admin/forms/FormRow';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import {Checkbox, TextInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {getTranslatedChoices} from 'utils/i18n';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';
import ErrorList from 'components/admin/forms/ErrorList';

import TinyMCEEditor from './Editor';
import {parseValidationErrors} from './utils';

const EMAIL_OPTIONS = [
  [
    'global_email',
    defineMessage({
      description: 'global_email option label',
      defaultMessage: 'Global email',
    }),
  ],
  [
    'form_specific_email',
    defineMessage({
      description: 'form_specific_email option label',
      defaultMessage: 'Form specific email',
    }),
  ],
  [
    'no_email',
    defineMessage({
      description: 'no_email option label',
      defaultMessage: 'No email',
    }),
  ],
];

const Confirmation = ({
  pageTemplate = '',
  displayMainWebsiteLink = false,
  emailOption = 'global_email',
  emailTemplate = {},
  onChange,
}) => {
  const intl = useIntl();
  const emailOptions = getTranslatedChoices(intl, EMAIL_OPTIONS);

  const formValidationErrors = parseValidationErrors(useContext(ValidationErrorContext), 'form');

  const {subject, content} = emailTemplate;

  const onCheckboxChange = (event, currentValue) => {
    const {
      target: {name},
    } = event;
    onChange({target: {name, value: !currentValue}});
  };

  return (
    <div className="confirmation-page">
      <Fieldset
        title={
          <FormattedMessage
            defaultMessage="Submission confirmation template"
            description="Submission confirmation fieldset title"
          />
        }
      >
        {formValidationErrors.submissionConfirmationTemplate?.nonFieldErrors && (
          <ErrorList classNamePrefix="confirmation-page">
            {formValidationErrors.submissionConfirmationTemplate.nonFieldErrors}
          </ErrorList>
        )}
        <FormRow>
          <Field
            name="form.submissionConfirmationTemplate"
            label={
              <FormattedMessage
                defaultMessage="Page content"
                description="Confirmation page content label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="The content of the submission confirmation page. It can contain variables that will be templated from the submitted form data. If not specified, the global template will be used."
                description="Confirmation template help text"
              />
            }
          >
            <TinyMCEEditor
              content={pageTemplate}
              onEditorChange={(newValue, editor) =>
                onChange({target: {name: 'form.submissionConfirmationTemplate', value: newValue}})
              }
            />
          </Field>
        </FormRow>
        <FormRow>
          <Checkbox
            name="form.displayMainWebsiteLink"
            label={
              <FormattedMessage
                defaultMessage="Display main website link"
                description="Display main website link field label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Whether to show a link to the main website on the confirmation page."
                description="Display main website link help text"
              />
            }
            checked={displayMainWebsiteLink}
            onChange={event => onCheckboxChange(event, displayMainWebsiteLink)}
          />
        </FormRow>
      </Fieldset>
      <Fieldset
        title={
          <FormattedMessage
            defaultMessage="Submission confirmation email template"
            description="Submission confirmation email fieldset title"
          />
        }
      >
        {formValidationErrors.confirmationEmailTemplate?.nonFieldErrors && (
          <ErrorList classNamePrefix="confirmation-page">
            {formValidationErrors.confirmationEmailTemplate.nonFieldErrors}
          </ErrorList>
        )}
        <FormRow>
          <Field
            name="form.confirmationEmailTemplate.subject"
            label={
              <FormattedMessage
                defaultMessage="Subject"
                description="Confirmation Email Subject label"
              />
            }
          >
            <TextInput value={subject || ''} onChange={onChange} maxLength="1000" />
          </Field>
        </FormRow>
        <FormRow>
          <Field
            name="form.confirmationEmailTemplate.content"
            label={
              <FormattedMessage
                defaultMessage="Content"
                description="Confirmation Email Content label"
              />
            }
          >
            <TinyMCEEditor
              content={content}
              onEditorChange={(newValue, editor) =>
                onChange({
                  target: {name: 'form.confirmationEmailTemplate.content', value: newValue},
                })
              }
            />
          </Field>
        </FormRow>
        <FormRow>
          <Field
            name="form.confirmationEmailOption"
            label={
              <FormattedMessage
                defaultMessage="Email option"
                description="Form confirmation email label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Will send the email specified."
                description="Form confirmation email help text"
              />
            }
          >
            <Select
              name="form.confirmationEmailOption"
              choices={emailOptions}
              value={emailOption}
              onChange={onChange}
            />
          </Field>
        </FormRow>
      </Fieldset>
    </div>
  );
};

Confirmation.propTypes = {
  pageTemplate: PropTypes.string,
  displayMainPage: PropTypes.bool,
  emailOption: PropTypes.string,
  emailTemplate: PropTypes.object,
  onChange: PropTypes.func.isRequired,
};

export default Confirmation;
