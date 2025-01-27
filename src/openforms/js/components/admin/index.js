import React from 'react';
import ReactDOM from 'react-dom';
import ReactModal from 'react-modal';
import {IntlProvider} from 'react-intl';

import jsonScriptToVar from 'utils/json-script';

import {FormCreationForm} from './form_design/form-creation-form';
import {TinyMceContext, FeatureFlagsContext} from './form_design/Context';
import FormVersionsTable from './form_versions/FormVersionsTable';
import './plugin_configuration';
import './form-category';
import './submissions/filter';

import Debug from './debug';
import SessionStatus from './SessionStatus';
import {getIntlProviderProps} from './i18n';
import setSeleniumMarker from './selenium';

const mountForm = intlProps => {
  const formCreationFormNodes = document.getElementsByClassName('react-form-create');
  if (!formCreationFormNodes.length) return;

  for (const formCreationFormNode of formCreationFormNodes) {
    const {csrftoken, formUuid, formUrl, tinymceUrl, formHistoryUrl} = formCreationFormNode.dataset;

    const featureFlags = jsonScriptToVar('feature-flags');

    ReactModal.setAppElement(formCreationFormNode);

    ReactDOM.render(
      <IntlProvider {...intlProps}>
        <TinyMceContext.Provider value={tinymceUrl}>
          <FeatureFlagsContext.Provider value={featureFlags}>
            <FormCreationForm
              csrftoken={csrftoken}
              formUuid={formUuid}
              formUrl={formUrl}
              formHistoryUrl={formHistoryUrl}
            />
          </FeatureFlagsContext.Provider>
        </TinyMceContext.Provider>
      </IntlProvider>,
      formCreationFormNode
    );
  }
};

const mountFormVersions = intlProps => {
  const formVersionsNodes = document.getElementsByClassName('react-form-versions-table');
  if (!formVersionsNodes.length) return;

  for (const formVersionsNode of formVersionsNodes) {
    const {formUuid, csrftoken, currentRelease} = formVersionsNode.dataset;

    ReactDOM.render(
      <IntlProvider {...intlProps}>
        <FormVersionsTable
          csrftoken={csrftoken}
          formUuid={formUuid}
          currentRelease={currentRelease}
        />
      </IntlProvider>,
      formVersionsNode
    );
  }
};

const mountDebugComponent = () => {
  const node = document.getElementById('react');
  if (!node) return;
  ReactDOM.render(<Debug />, node);
};

const mountSessionStatus = intlProps => {
  const nodes = document.querySelectorAll('.react-session-status');
  for (const node of nodes) {
    ReactDOM.render(
      <IntlProvider {...intlProps}>
        <SessionStatus />
      </IntlProvider>,
      node
    );
  }
};

const bootstrapApplication = async () => {
  const intlProviderProps = await getIntlProviderProps();
  mountSessionStatus(intlProviderProps);
  mountForm(intlProviderProps);
  mountFormVersions(intlProviderProps);
};

bootstrapApplication();
mountDebugComponent();

// this must be the last call in the script, as we rely on the marker being absent
// to detect crashes in the JS via Selenium tests
setSeleniumMarker();
