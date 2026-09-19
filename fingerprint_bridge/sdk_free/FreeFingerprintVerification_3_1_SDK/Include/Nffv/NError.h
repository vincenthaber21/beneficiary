#ifndef N_ERROR_H_INCLUDED
#define N_ERROR_H_INCLUDED

#include <Nffv/NDefs.h>

#ifdef N_CPP
extern "C"
{
#endif

#define N_OK                               0
#define N_E_FAILED                        -1
  #define N_E_CORE                        -2
    #define N_E_ABANDONED_MUTEX          -25
    #define N_E_AGGREGATE                -33
    #define N_E_ARGUMENT                 -10
      #define N_E_ARGUMENT_NULL          -11
      #define N_E_ARGUMENT_OUT_OF_RANGE  -12
      #define N_E_INVALID_ENUM_ARGUMENT  -16
    #define N_E_ARITHMETIC               -17
      #define N_E_OVERFLOW                -8
    #define N_E_BAD_IMAGE_FORMAT         -26
    #define N_E_DLL_NOT_FOUND            -27
    #define N_E_ENTRY_POINT_NOT_FOUND    -28
    #define N_E_FORMAT                   -13
      #define N_E_FILE_FORMAT            -29
    #define N_E_INDEX_OUT_OF_RANGE        -9
    #define N_E_INVALID_CAST             -18
    #define N_E_INVALID_OPERATION         -7
    #define N_E_IO                       -14
      #define N_E_DIRECTORY_NOT_FOUND    -19
      #define N_E_DRIVE_NOT_FOUND        -20
      #define N_E_END_OF_STREAM          -15
      #define N_E_FILE_NOT_FOUND         -21
      #define N_E_FILE_LOAD              -22
      #define N_E_PATH_TOO_LONG          -23
      #define N_E_SOCKET                 -31
    #define N_E_KEY_NOT_FOUND            -32
    #define N_E_NOT_IMPLEMENTED           -5
    #define N_E_NOT_SUPPORTED             -6
    #define N_E_NULL_REFERENCE            -3
    #define N_E_OPERATION_CANCELED       -34
    #define N_E_OUT_OF_MEMORY             -4
    #define N_E_SECURITY                 -24
    #define N_E_TIMEOUT                  -30

    #define N_E_EXTERNAL                 -90
      #define N_E_CLR                    -93
      #define N_E_COM                    -92
      #define N_E_CPP                    -96
      #define N_E_JVM                    -97
      #define N_E_MAC                    -95
      #define N_E_SYS                    -94
      #define N_E_WIN32                  -91

    #define N_E_NOT_ACTIVATED           -200

#define NFailed(result) ((result) < 0)
#define NSucceeded(result) ((result) >= 0)

#ifdef N_CPP
}
#endif

#endif // !N_ERROR_H_INCLUDED
