/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/app/trends', '<rootDir>/app/compare', '<rootDir>/app/commandk'],
  moduleFileExtensions: ['ts', 'tsx', 'js'],
};
