import React from 'react';
import PropTypes from 'prop-types';

const ValidationErrorContext = React.createContext([]);
ValidationErrorContext.displayName = 'ValidationErrorContext';

const ValidationErrorsProvider = ({children, errors = []}) => {
  return (
    <ValidationErrorContext.Provider value={errors}>{children}</ValidationErrorContext.Provider>
  );
};

const errorArray = props => {
  const errorMsg = 'Invalid error passed to ValidationErrorsProvider.';

  if (props.length !== 2) return new Error(`${errorMsg} It should have length 2`);

  if (typeof props[0] !== 'string')
    return new Error(`${errorMsg} The error key should be a string.`);
  if (!(typeof props[1] === 'string' || props[1].defaultMessage))
    return new Error(`${errorMsg} The error msg should be a string or and intl object.`);
};

ValidationErrorsProvider.propTypes = {
  errors: PropTypes.arrayOf(PropTypes.arrayOf(errorArray)),
};

export {ValidationErrorsProvider, ValidationErrorContext};
export default ValidationErrorsProvider;
