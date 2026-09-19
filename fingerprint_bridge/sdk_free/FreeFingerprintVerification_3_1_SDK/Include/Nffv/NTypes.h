#ifndef N_TYPES_H_INCLUDED
#define N_TYPES_H_INCLUDED

#include <Nffv/NDefs.h>

#ifdef N_CPP
extern "C"
{
#endif
	
#ifdef N_MSVC
	#define N_VA_LIST_INIT = 0
	#if _MSC_VER < 1800
		#define va_copy(dest, src) (dest) = (src)
	#endif
#else
	#define N_VA_LIST_INIT = { 0 }
#endif

#define N_DECLATE_PRIMITIVE(name, size) typedef struct { union { void * ptr; /* for correct alignment */ NByte data[size]; } unused; } name;
#define N_DECLARE_HANDLE(name) typedef struct name##_ { int unused; } * name;

#ifdef N_MSVC
	typedef signed __int32 NResult;
#else
	typedef signed int NResult;
#endif

#define N_TYPE_OF(name) N_JOIN_SYMBOLS(name, TypeOf)

#define N_DECLARE_TYPE(name) \
	NResult N_API name##TypeOf(HNType * phValue);

#define N_DECLARE_STATIC_OBJECT_TYPE(name) \
	N_DECLARE_TYPE(name)

#ifdef N_CPP
	#define N_DECLARE_OBJECT_TYPE(name, baseName) \
		typedef class H##name##_ : public H##baseName##_ { } * H##name;\
		N_DECLARE_STATIC_OBJECT_TYPE(name)
#else
	#define N_DECLARE_OBJECT_TYPE(name, baseName) \
		typedef H##baseName H##name;\
		N_DECLARE_STATIC_OBJECT_TYPE(name)
#endif

N_DECLARE_HANDLE(HNObject)
N_DECLARE_OBJECT_TYPE(NType, NObject)
N_DECLARE_OBJECT_TYPE(NObjectPart, NObject)
N_DECLARE_TYPE(NObject)

#define N_DECLARE_HANDLE_TYPE(name) \
	N_DECLARE_HANDLE(H##name)\
	N_DECLARE_TYPE(name)

N_DECLARE_HANDLE_TYPE(NString)
N_DECLARE_HANDLE_TYPE(NCallback)

N_DECLARE_TYPE(NResult)

#ifdef N_MSVC
	typedef unsigned __int8  NUInt8;
	typedef signed   __int8  NInt8;
	typedef unsigned __int16 NUInt16;
	typedef signed   __int16 NInt16;
	typedef unsigned __int32 NUInt32;
	typedef signed   __int32 NInt32;

	#define N_UINT8_MIN 0x00ui8
	#define N_UINT8_MAX 0xFFui8
	#define N_INT8_MIN 0x80i8
	#define N_INT8_MAX 0x7Fi8
	#define N_UINT16_MIN 0x0000ui16
	#define N_UINT16_MAX 0xFFFFui16
	#define N_INT16_MIN 0x8000i16
	#define N_INT16_MAX 0x7FFFi16
	#define N_UINT32_MIN 0x00000000ui32
	#define N_UINT32_MAX 0xFFFFFFFFui32
	#define N_INT32_MIN 0x80000000i32
	#define N_INT32_MAX 0x7FFFFFFFi32
#else
	typedef unsigned char  NUInt8;
	typedef signed   char  NInt8;
	typedef unsigned short NUInt16;
	typedef signed   short NInt16;
	typedef unsigned int   NUInt32;
	typedef signed   int   NInt32;

	#define N_UINT8_MIN ((NUInt8)0x00u)
	#define N_UINT8_MAX ((NUInt8)0xFFu)
	#define N_INT8_MIN ((NInt8)0x80)
	#define N_INT8_MAX ((NInt8)0x7F)
	#define N_UINT16_MIN ((NUInt16)0x0000u)
	#define N_UINT16_MAX ((NUInt16)0xFFFFu)
	#define N_INT16_MIN ((NInt16)0x8000)
	#define N_INT16_MAX ((NInt16)0x7FFF)
	#define N_UINT32_MIN 0x00000000u
	#define N_UINT32_MAX 0xFFFFFFFFu
	#define N_INT32_MIN ((NInt32)0x80000000)
	#define N_INT32_MAX 0x7FFFFFFF
#endif
N_DECLARE_TYPE(NUInt8)
N_DECLARE_TYPE(NInt8)
N_DECLARE_TYPE(NUInt16)
N_DECLARE_TYPE(NInt16)
N_DECLARE_TYPE(NUInt32)
N_DECLARE_TYPE(NInt32)

#ifndef N_NO_INT_64
	#ifdef N_MSVC
		typedef unsigned __int64 NUInt64;
		typedef signed   __int64 NInt64;

		#define N_UINT64_MIN 0x0000000000000000ui64
		#define N_UINT64_MAX 0xFFFFFFFFFFFFFFFFui64
		#define N_INT64_MIN 0x8000000000000000i64
		#define N_INT64_MAX 0x7FFFFFFFFFFFFFFFi64
	#else
		typedef unsigned long long NUInt64;
		typedef signed   long long NInt64;

		#define N_UINT64_MIN 0x0000000000000000ull
		#define N_UINT64_MAX 0xFFFFFFFFFFFFFFFFull
		#define N_INT64_MIN ((NInt64)0x8000000000000000ull)
		#define N_INT64_MAX 0x7FFFFFFFFFFFFFFFll
	#endif
	N_DECLARE_TYPE(NUInt64)
	N_DECLARE_TYPE(NInt64)
#endif


typedef NUInt8 NByte;
typedef NInt8 NSByte;
typedef NUInt16 NUShort;
typedef NInt16 NShort;
typedef NUInt32 NUInt;
typedef NInt32 NInt;

#ifndef N_NO_INT_64
	typedef NUInt64 NULong;
	typedef NInt64 NLong;
#endif

#define N_BYTE_MIN N_UINT8_MIN
#define N_BYTE_MAX N_UINT8_MAX
#define N_SBYTE_MIN N_INT8_MIN
#define N_SBYTE_MAX N_INT8_MAX
#define N_USHORT_MIN N_UINT16_MIN
#define N_USHORT_MAX N_UINT16_MAX
#define N_SHORT_MIN N_INT16_MIN
#define N_SHORT_MAX N_INT16_MAX
#define N_UINT_MIN N_UINT32_MIN
#define N_UINT_MAX N_UINT32_MAX
#define N_INT_MIN N_INT32_MIN
#define N_INT_MAX N_INT32_MAX

#ifndef N_NO_INT_64
	#define N_ULONG_MIN N_UINT64_MIN
	#define N_ULONG_MAX N_UINT64_MAX
	#define N_LONG_MIN N_INT64_MIN
	#define N_LONG_MAX N_INT64_MAX
#endif

#ifndef N_NO_FLOAT
	typedef float NSingle;
	typedef double NDouble;
	N_DECLARE_TYPE(NSingle)
	N_DECLARE_TYPE(NDouble)

	#define N_SINGLE_MIN -3.402823466e+38F
	#define N_SINGLE_MAX 3.402823466e+38F
	#define N_SINGLE_EPSILON 1.192092896e-07F
	#define N_DOUBLE_MIN -1.7976931348623158e+308
	#define N_DOUBLE_MAX 1.7976931348623158e+308
	#define N_DOUBLE_EPSILON 2.2204460492503131e-016

	typedef NSingle NFloat;

	#define N_FLOAT_MIN N_SINGLE_MIN
	#define N_FLOAT_MAX N_SINGLE_MAX
	#define N_FLOAT_EPSILON N_SINGLE_EPSILON
#endif

typedef NInt NBoolean;
N_DECLARE_TYPE(NBoolean)

#define NTrue 1
#define NFalse 0

typedef NBoolean NBool;

typedef char NAChar;

#if defined(N_WINDOWS) || (defined(__SIZEOF_WCHAR_T__) && __SIZEOF_WCHAR_T__ == 2)
	#define N_WCHAR_SIZE 2

	#if !defined(N_NO_UNICODE) && !defined(_WCHAR_T_DEFINED)
		typedef NUShort NWChar;
	#endif
#else // !defined(N_WINDOWS) && (!defined(__SIZEOF_WCHAR_T__) || __SIZEOF_WCHAR_T__ != 2)
	#define N_WCHAR_SIZE 4

	#if !defined(N_NO_UNICODE) && !defined(_WCHAR_T_DEFINED) && !defined(_WCHAR_T)
		#ifdef N_CPP
			typedef wchar_t NWChar;
		#else
			#ifdef __WCHAR_TYPE__
				typedef __WCHAR_TYPE__ NWChar;
			#else
				typedef int NWChar;
			#endif
		#endif
	#endif
#endif // !defined(N_WINDOWS) && (!defined(__SIZEOF_WCHAR_T__) || __SIZEOF_WCHAR_T__ != 2)

#if !defined(N_NO_UNICODE) && defined(_WCHAR_T_DEFINED) || defined(_WCHAR_T)
	typedef wchar_t NWChar;
#endif

N_DECLARE_TYPE(NAChar)
#ifndef N_NO_UNICODE
N_DECLARE_TYPE(NWChar)
#endif
#ifdef N_DOCUMENTATION
N_DECLARE_TYPE(NChar)
#endif
#ifdef N_UNICODE
	typedef NWChar NChar;
	#define NCharTypeOf NWCharTypeOf
#else
	typedef NAChar NChar;
	#define NCharTypeOf NACharTypeOf
#endif

#ifdef N_64
	typedef NUInt64 NSizeType;
	typedef NInt64 NSSizeType;

	#define N_SIZE_TYPE_MIN N_UINT64_MIN
	#define N_SIZE_TYPE_MAX N_UINT64_MAX
	#define N_SSIZE_TYPE_MIN N_INT64_MIN
	#define N_SSIZE_TYPE_MAX N_INT64_MAX
#else
	#ifdef N_MSVC
		typedef __w64 NUInt32 NSizeType;
		typedef __w64 NInt32 NSSizeType;
	#else
		typedef NUInt32 NSizeType;
		typedef NInt32 NSSizeType;
	#endif

	#define N_SIZE_TYPE_MIN N_UINT32_MIN
	#define N_SIZE_TYPE_MAX N_UINT32_MAX
	#define N_SSIZE_TYPE_MIN N_INT32_MIN
	#define N_SSIZE_TYPE_MAX N_INT32_MAX
#endif
N_DECLARE_TYPE(NSizeType)
N_DECLARE_TYPE(NSSizeType)

#define N_PTR_SIZE sizeof(void *)
N_DECLARE_TYPE(NPointer)

#ifndef NULL
	#define NULL 0
#endif

#if defined(N_MSVC) && !defined(N_NVCC)
#define N_UNREFERENCED_PARAMETER(parameter) (parameter)
#else
#define N_UNREFERENCED_PARAMETER(parameter) (void)(parameter)
#endif
#define N_UNUSED_VARIABLE(variable) N_UNREFERENCED_PARAMETER(variable)
#define N_SOMETIMES_UNREFERENCED_PARAMETER(parameter) N_UNREFERENCED_PARAMETER(parameter)
#define N_SOMETIMES_UNUSED_VARIABLE(variable) N_UNUSED_VARIABLE(variable)

typedef void * NHandle;
N_DECLARE_TYPE(NHandle)

#ifdef N_CPP
}
#endif

#endif // !N_TYPES_H_INCLUDED
