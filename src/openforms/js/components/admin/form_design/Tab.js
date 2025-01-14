import React from 'react';
import {useIntl} from 'react-intl';
import {Tab as ReactTab} from 'react-tabs';
import PropTypes from 'prop-types';

import FAIcon from 'components/admin/FAIcon';

const Tab = ({hasErrors = false, children, ...props}) => {
  const intl = useIntl();
  const customProps = {
    className: ['react-tabs__tab', {'react-tabs__tab--has-errors': hasErrors}],
  };
  const allProps = {...props, ...customProps};
  const title = intl.formatMessage({
    defaultMessage: 'There are validation errors',
    description: 'Tab validation errors icon title',
  });
  return (
    <ReactTab {...allProps}>
      {children}
      {hasErrors ? (
        <FAIcon icon="exclamation-circle" extraClassname="react-tabs__error-badge" title={title} />
      ) : null}
    </ReactTab>
  );
};
Tab.tabsRole = 'Tab';

Tab.propTypes = {
  hasErrors: PropTypes.bool,
};

export default Tab;
